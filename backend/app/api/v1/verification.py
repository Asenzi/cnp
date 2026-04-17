import json
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_hex
from typing import Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id, get_current_user_id_from_header_or_query
from app.core.exceptions import BusinessException
from app.core.response import success_response
from app.crud import get_user_by_id, get_user_real_name_profile, get_user_verification
from app.schemas.verification import (
    BusinessCardVerificationSubmitRequest,
    EnterpriseVerificationSubmitRequest,
    RealNameVerificationSubmitRequest,
    TencentRealNameFinishRequest,
    TencentRealNameStartRequest,
)
from app.verification.constants import VerificationType
from app.verification.files import (
    ID_CARD_STORAGE_DIR,
    build_private_id_card_file_ref,
    guess_media_type,
    resolve_id_card_file_path,
)
from app.verification.service import (
    get_user_real_name_verification_detail,
    get_user_verification_overview,
    submit_user_verification,
)
from app.verification.tencent_real_name import (
    finish_tencent_real_name_verification,
    start_tencent_real_name_verification,
)

router = APIRouter(prefix='/verification', tags=['Verification'])

STATIC_DIR = Path(__file__).resolve().parents[3] / 'static'
LICENSE_UPLOAD_DIR = STATIC_DIR / 'uploads' / 'licenses'

MAX_LICENSE_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_ID_CARD_FILE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_LICENSE_CONTENT_TYPES = {'image/jpeg', 'image/png', 'application/pdf'}
ALLOWED_ID_CARD_CONTENT_TYPES = {'image/jpeg', 'image/png'}
CONTENT_TYPE_EXTENSION_MAP = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'application/pdf': '.pdf',
}


def _require_current_user(db: Session, current_user_pk: int):
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message='用户不存在', code=4041, status_code=404)
    return user


def _load_real_name_file_url(*, record, profile, side: Literal['front', 'back']) -> str:
    if profile is not None:
        return str(profile.id_front_url if side == 'front' else profile.id_back_url).strip()
    if record is None or not record.submit_payload_json:
        return ''
    try:
        payload = json.loads(record.submit_payload_json)
    except (TypeError, ValueError):
        return ''
    if not isinstance(payload, dict):
        return ''
    key = 'id_front_url' if side == 'front' else 'id_back_url'
    return str(payload.get(key) or '').strip()


@router.get('/me', summary="Get current user's verification overview")
def get_my_verification_overview(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    overview = get_user_verification_overview(db=db, user=user)
    return success_response(data=overview.model_dump(mode='json'))


@router.get('/real-name/detail', summary="Get current user's real-name verification detail")
def get_my_real_name_verification_detail(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    detail = get_user_real_name_verification_detail(db=db, user=user)
    return success_response(data=detail.model_dump(mode='json'))


@router.get('/real-name/files/{side}', summary='Preview current user real-name id-card file')
def get_my_real_name_id_card_file(
    side: Literal['front', 'back'],
    user_id: int = Depends(get_current_user_id_from_header_or_query),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    record = get_user_verification(db=db, user_pk=int(user.id), verify_type=VerificationType.REAL_NAME.value)
    profile = get_user_real_name_profile(db=db, user_pk=int(user.id))
    file_url = _load_real_name_file_url(record=record, profile=profile, side=side)
    if not file_url:
        raise BusinessException(message='实名认证资料不存在', code=4346, status_code=404)

    file_path = resolve_id_card_file_path(file_url)
    return FileResponse(
        path=file_path,
        media_type=guess_media_type(file_path),
        filename=file_path.name,
        headers={'Cache-Control': 'private, no-store'},
    )


@router.post('/real-name/id-card-file', summary='Upload real-name id-card image file')
async def upload_real_name_id_card_file(
    side: Literal['front', 'back'] = Query(..., description='ID card side: front/back'),
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)

    content_type = (file.content_type or '').lower().strip()
    if content_type not in ALLOWED_ID_CARD_CONTENT_TYPES:
        raise BusinessException(message='身份证照片仅支持 JPG/PNG', code=4341, status_code=400)

    file_bytes = await file.read()
    if not file_bytes:
        raise BusinessException(message='上传文件为空', code=4342, status_code=400)

    if len(file_bytes) > MAX_ID_CARD_FILE_SIZE_BYTES:
        raise BusinessException(message='身份证照片不能超过 10MB', code=4343, status_code=400)

    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in {'.jpg', '.jpeg', '.png'}:
        suffix = CONTENT_TYPE_EXTENSION_MAP.get(content_type, '.jpg')

    ID_CARD_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{side}_{token_hex(4)}{suffix}"
    save_path = ID_CARD_STORAGE_DIR / file_name
    save_path.write_bytes(file_bytes)

    file_ref = build_private_id_card_file_ref(file_name)
    display_name = (file.filename or f'身份证-{side}').strip() or f'身份证-{side}'
    if len(display_name) > 128:
        display_name = display_name[:128]

    return success_response(
        data={
            'side': side,
            'name': display_name,
            'url': file_ref,
            'size': len(file_bytes),
        },
        message='身份证照片上传成功',
    )


@router.post('/enterprise/license-file', summary='Upload enterprise license file')
async def upload_enterprise_license_file(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)

    content_type = (file.content_type or '').lower().strip()
    if content_type not in ALLOWED_LICENSE_CONTENT_TYPES:
        raise BusinessException(message='营业执照文件仅支持 JPG/PNG/PDF', code=4331, status_code=400)

    file_bytes = await file.read()
    if not file_bytes:
        raise BusinessException(message='上传文件为空', code=4332, status_code=400)

    if len(file_bytes) > MAX_LICENSE_FILE_SIZE_BYTES:
        raise BusinessException(message='营业执照文件不能超过 10MB', code=4333, status_code=400)

    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in {'.jpg', '.jpeg', '.png', '.pdf'}:
        suffix = CONTENT_TYPE_EXTENSION_MAP.get(content_type, '.pdf')

    LICENSE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{token_hex(4)}{suffix}"
    save_path = LICENSE_UPLOAD_DIR / file_name
    save_path.write_bytes(file_bytes)

    relative_url = f'/static/uploads/licenses/{file_name}'
    display_name = (file.filename or '营业执照').strip() or '营业执照'
    if len(display_name) > 128:
        display_name = display_name[:128]

    return success_response(
        data={
            'name': display_name,
            'url': relative_url,
            'size': len(file_bytes),
        },
        message='营业执照上传成功',
    )


@router.post('/real-name/submit', summary='Submit real-name verification')
def submit_real_name_verification(
    payload: RealNameVerificationSubmitRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    item = submit_user_verification(
        db=db,
        user=user,
        verify_type=VerificationType.REAL_NAME,
        payload=payload.model_dump(),
    )
    return success_response(data=item.model_dump(mode='json'), message='实名认证资料已提交审核')


@router.post('/real-name/tencent/start', summary='Start Tencent real-name verification')
def start_tencent_real_name_flow(
    payload: TencentRealNameStartRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    data = start_tencent_real_name_verification(
        db=db,
        user=user,
        real_name=payload.real_name,
        id_number=payload.id_number,
    )
    return success_response(data=data.model_dump(mode='json'), message='实名认证会话已创建')


@router.post('/real-name/tencent/finish', summary='Finish Tencent real-name verification')
def finish_tencent_real_name_flow(
    payload: TencentRealNameFinishRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    data = finish_tencent_real_name_verification(
        db=db,
        user=user,
        provider_biz_token=payload.provider_biz_token,
    )
    return success_response(data=data.model_dump(mode='json'), message='实名认证结果已更新')


@router.post('/enterprise/submit', summary='Submit enterprise verification')
def submit_enterprise_verification(
    payload: EnterpriseVerificationSubmitRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    item = submit_user_verification(
        db=db,
        user=user,
        verify_type=VerificationType.ENTERPRISE,
        payload=payload.model_dump(),
    )
    return success_response(data=item.model_dump(mode='json'), message='企业认证资料已提交审核')


@router.post('/business-card/submit', summary='Submit business-card verification')
def submit_business_card_verification(
    payload: BusinessCardVerificationSubmitRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    item = submit_user_verification(
        db=db,
        user=user,
        verify_type=VerificationType.BUSINESS_CARD,
        payload=payload.model_dump(),
    )
    return success_response(data=item.model_dump(mode='json'), message='名片认证资料已提交审核')
