from fastapi import APIRouter, Query, HTTPException
import httpx
from app.core.config import settings
from app.core.response import success_response

router = APIRouter(prefix="/map", tags=["Map"])


async def _reverse_geocode_impl(latitude: float, longitude: float):
    """
    逆地理编码实现
    """
    if not settings.QQ_MAP_KEY:
        raise HTTPException(status_code=500, detail="地图服务未配置")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://apis.map.qq.com/ws/geocoder/v1/",
                params={
                    "key": settings.QQ_MAP_KEY,
                    "location": f"{latitude},{longitude}",
                    "get_poi": 0,
                },
                timeout=10.0,
            )

            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="地图服务请求失败")

            data = response.json()

            if data.get("status") != 0:
                raise HTTPException(
                    status_code=400,
                    detail=data.get("message", "地图服务返回错误")
                )

            # 提取城市信息
            city = data.get("result", {}).get("address_component", {}).get("city", "")
            if not city:
                raise HTTPException(status_code=404, detail="未找到城市信息")

            # 去掉"市"字
            city = city.replace("市", "")

            return success_response(data={
                "city": city,
                "raw": data  # 返回完整数据供调试
            })

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="地图服务请求超时")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"地图服务请求失败: {str(e)}")


@router.get("/geocoder/reverse", summary="Reverse geocode (lat/lng to address)")
async def reverse_geocode(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
):
    """
    通过经纬度获取地址信息（腾讯地图逆地址解析代理）
    """
    return await _reverse_geocode_impl(latitude, longitude)


@router.get("/reverse-geocode", summary="Reverse geocode (lat/lng to address) - alias")
async def reverse_geocode_alias(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
):
    """
    通过经纬度获取地址信息（腾讯地图逆地址解析代理）
    前端使用的路径别名
    """
    return await _reverse_geocode_impl(latitude, longitude)
