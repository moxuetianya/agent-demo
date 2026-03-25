"""
Base64 解码模块
功能：实现 base64 解码函数，处理编码字符串并返回原始字符串
"""

import base64


def decode_base64(encoded_string):
    """
    解码 base64 编码的字符串
    
    参数:
        encoded_string: base64 编码的字符串
        
    返回:
        解码后的原始字符串
        
    异常:
        ValueError: 当输入包含非法字符或填充错误时
    """
    if not isinstance(encoded_string, str):
        raise TypeError(f"输入必须是字符串类型，收到 {type(encoded_string).__name__}")
    
    # 去除首尾空白字符
    encoded_string = encoded_string.strip()
    
    if not encoded_string:
        raise ValueError("输入字符串不能为空")
    
    # 验证 base64 字符集 (A-Z, a-z, 0-9, +, /, =)
    base64_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    
    for char in encoded_string:
        if char not in base64_chars:
            raise ValueError(f"非法字符 '{char}' 在 base64 编码中")
    
    try:
        # 执行 base64 解码
        decoded_bytes = base64.b64decode(encoded_string, validate=True)
        
        # 尝试将字节转换为字符串 (UTF-8)
        try:
            decoded_string = decoded_bytes.decode('utf-8')
            return decoded_string
        except UnicodeDecodeError:
            # 如果不是有效的 UTF-8，返回原始字节（以字符串形式表示）
            return f"[二进制数据，长度 {len(decoded_bytes)} 字节]"
            
    except base64.binascii.Error as e:
        raise ValueError(f"Base64 解码错误: {str(e)}")


def test_decode_base64():
    """测试 decode_base64 函数"""
    # 测试用例
    test_cases = [
        # (输入, 期望输出)
        ("SGVsbG8gV29ybGQh", "Hello World!"),  # 基本测试
        ("SGVsbG8gV29ybGQh\n", "Hello World!"),  # 带换行符
        ("  SGVsbG8gV29ybGQh  ", "Hello World!"),  # 带空格
        ("UGV0ZXI=", "Peter"),  # 带填充 =
        ("Zg==", "f"),  # 短字符串
        ("", None),  # 空字符串 (应抛出异常)
        ("!@#$", None),  # 非法字符 (应抛出异常)
    ]
    
    print("=" * 50)
    print("Base64 解码测试")
    print("=" * 50)
    
    for encoded, expected in test_cases:
        try:
            result = decode_base64(encoded)
            status = "✓ PASS" if result == expected else f"✗ FAIL (got: {result})"
            print(f"测试: '{encoded}' -> '{result}' {status}")
        except Exception as e:
            if expected is None:
                print(f"测试: '{encoded}' -> 正确抛出异常: {e} ✓ PASS")
            else:
                print(f"测试: '{encoded}' -> 意外异常: {e} ✗ FAIL")
    
    print("=" * 50)


if __name__ == "__main__":
    test_decode_base64()
