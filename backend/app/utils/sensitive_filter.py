# ============================================================================
# 文件功能：敏感信息过滤工具（手机号、身份证、user_id 脱敏），防止用户隐私数据（手机号、身份证、user_id）在日志或返回给前端时泄露。
# 谁调用它：routes.py（返回数据前），中返回数据前调用，确保前端看到的 user_id 已脱敏；同时在后端日志中也会过滤。
# 它调用谁：re, logger
# ============================================================================
import re
from app.utils.logger import logger

def mask_phone(phone: str) -> str:
    """
    手机号中间4位掩码，例如 138****1234
    参数: phone: 手机号字符串
    返回: 脱敏后的手机号
    """
    if not phone or len(phone) < 7:
        return phone
    # 匹配 3位-4位-4位 格式
    return re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', str(phone))

def mask_id_card(id_card: str) -> str:
    """身份证号掩码，只显示前6后4"""
    if not id_card or len(id_card) < 10:
        return id_card
    return id_card[:6] + "********" + id_card[-4:]

def mask_user_id(user_id: str) -> str:
    """
    用户唯一编码掩码，9位编码显示前3后2，中间4个星号
    例如 abc123456 -> abc****56
    参数: user_id: 用户ID字符串
    返回: 脱敏后的用户ID
    """
    if not user_id:
        return user_id
    uid_str = str(user_id)
    length = len(uid_str)
    if length == 9:
        # 9位：前3后2，中间4个星号
        return uid_str[:3] + "****" + uid_str[-2:]
    elif length >= 8:
        # 其他长度（大于等于8）保持原逻辑：前3后4
        return uid_str[:3] + "****" + uid_str[-4:]
    else:
        # 过短则直接返回原值
        return uid_str

def filter_sensitive_data(data: any) -> any:
    """
    递归脱敏字典/列表中的敏感字段（phone, mobile, phone_num, id_card, user_id）
    参数: data: 任意数据结构（dict/list/基本类型）
    返回: 脱敏后的数据副本
    """
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            k_lower = k.lower()
            # 电话类字段：phone, mobile, phone_num
            if k_lower in ['phone', 'mobile', 'phone_num']:
                new_dict[k] = mask_phone(str(v))
                logger.debug(f"脱敏字段: {k}")
            elif k_lower in ['id_card', 'identity', 'identity_card']:
                new_dict[k] = mask_id_card(str(v))
                logger.debug(f"脱敏字段: {k}")
            elif k_lower == 'user_id':
                new_dict[k] = mask_user_id(str(v))
                logger.debug(f"脱敏字段: {k}")
            else:
                new_dict[k] = filter_sensitive_data(v)
        return new_dict
    elif isinstance(data, list):
        return [filter_sensitive_data(item) for item in data]
    else:
        return data

def filter_sql_sensitive(sql: str) -> str:
    """
    检查 SQL 中是否包含敏感字段，记录日志警告（不修改 SQL）
    """
    if re.search(r'\b(phone|phone_num|id_card|identity_card)\b', sql, re.IGNORECASE):
        logger.warning(f"SQL中包含敏感字段: {sql[:200]}")
    return sql