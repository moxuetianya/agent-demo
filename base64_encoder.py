"""
Base64 编码模块
功能：实现 base64 编码函数，将原始字符串编码为 base64 格式
"""

import base64


def encode_base64(input_string):
    """
    将字符串编码为 base64 格式
    
    参数:
        input_string: 原始字符串
        
    返回:
        base64 编码后的字符串
        
    异常:
        TypeError: 当输入不是字符串类型时
    """
    if not isinstance(input_string, str):
        raise TypeError(f"输入必须是字符串类型，收到 {type(input_string).__name__}")
    
    # 将字符串编码为 UTF-8 字节
    input_bytes = input_string.encode('utf-8')
    
    # 执行 base64 编码
    encoded_bytes = base64.b64encode(input_bytes)
    
    # 将编码后的字节转换为字符串
    encoded_string = encoded_bytes.decode('ascii')
    
    return encoded_string


def test_encode_base64():
    """测试 encode_base64 函数"""
    test_cases = [
        # (输入, 期望输出)
        ("Hello World!", "SGVsbG8gV29ybGQh"),
        ("Peter", "UGV0ZXI="),
        ("f", "Zg=="),
        ("", ""),
        ("你好，世界！", "5L2g5aW977yM5LiW55WM77yB"),  # 中文字符
        ("Test123!@#", "VGVzdDEyMyFAIw=="),  # 特殊字符
    ]
    
    print("=" * 50)
    print("Base64 编码测试")
    print("=" * 50)
    
    for input_str, expected in test_cases:
        try:
            result = encode_base64(input_str)
            status = "✓ PASS" if result == expected else f"✗ FAIL (got: {result})"
            print(f"测试: '{input_str}' -> '{result}' {status}")
        except Exception as e:
            print(f"测试: '{input_str}' -> 异常: {e} ✗ FAIL")
    
    print("=" * 50)


if __name__ == "__main__":
    test_encode_base64()
