"""
Base64 Encoder Demo

这是一个用于演示base64编码功能的Python模块。
支持各种字符编码，包括中文、特殊字符等。
"""

import base64
import binascii


def encode_base64(text):
    """
    将输入文本转换为base64编码字符串。
    
    Args:
        text: 输入文本，可以是字符串或字节类型
    
    Returns:
        str: base64编码后的字符串
    
    Raises:
        ValueError: 当输入无法进行有效编码时抛出
        TypeError: 当输入类型不支持时抛出
    
    Examples:
        >>> encode_base64("Hello World")
        'SGVsbG8gV29ybGQ='
        
        >>> encode_base64("你好，世界")
        '5L2g5aW977yM5LiW55WM'
    """
    try:
        # 如果输入是字符串，先编码为UTF-8字节
        if isinstance(text, str):
            text_bytes = text.encode('utf-8')
        # 如果输入已经是字节类型，直接使用
        elif isinstance(text, bytes):
            text_bytes = text
        else:
            raise TypeError(f"不支持的输入类型: {type(text).__name__}，期望str或bytes类型")
        
        # 使用base64进行编码
        encoded_bytes = base64.b64encode(text_bytes)
        
        # 将编码后的字节转换为字符串返回
        encoded_string = encoded_bytes.decode('ascii')
        
        return encoded_string
    
    except UnicodeEncodeError as e:
        raise ValueError(f"文本编码失败: {e}")
    except UnicodeDecodeError as e:
        raise ValueError(f"Base64编码结果解码失败: {e}")
    except binascii.Error as e:
        raise ValueError(f"Base64编码错误: {e}")


def decode_base64(encoded_text):
    """
    将base64编码字符串解码为原始文本。
    
    Args:
        encoded_text: base64编码的字符串
    
    Returns:
        str: 解码后的原始字符串
    
    Raises:
        ValueError: 当base64字符串无效时抛出
    """
    try:
        # 确保输入是字符串类型
        if isinstance(encoded_text, str):
            encoded_bytes = encoded_text.encode('ascii')
        elif isinstance(encoded_text, bytes):
            encoded_bytes = encoded_text
        else:
            raise TypeError(f"不支持的输入类型: {type(encoded_text).__name__}")
        
        # 解码base64
        decoded_bytes = base64.b64decode(encoded_bytes)
        
        # 将解码后的字节转换为UTF-8字符串
        decoded_string = decoded_bytes.decode('utf-8')
        
        return decoded_string
    
    except binascii.Error as e:
        raise ValueError(f"无效的base64字符串: {e}")
    except UnicodeDecodeError as e:
        raise ValueError(f"解码结果不是有效的UTF-8编码: {e}")


# 示例使用代码
if __name__ == "__main__":
    print("=" * 60)
    print("Base64 Encoder Demo - 使用示例")
    print("=" * 60)
    
    # 示例1: 英文文本
    english_text = "Hello, World!"
    print(f"\n[示例1] 英文文本: {english_text}")
    encoded = encode_base64(english_text)
    print(f"Base64编码: {encoded}")
    decoded = decode_base64(encoded)
    print(f"解码验证: {decoded}")
    
    # 示例2: 中文文本
    chinese_text = "你好，世界！这是Base64编码测试。"
    print(f"\n[示例2] 中文文本: {chinese_text}")
    encoded = encode_base64(chinese_text)
    print(f"Base64编码: {encoded}")
    decoded = decode_base64(encoded)
    print(f"解码验证: {decoded}")
    
    # 示例3: 特殊字符
    special_text = "Hello! @#$%^&*()_+ 特殊字符: ★☆✓"
    print(f"\n[示例3] 特殊字符: {special_text}")
    encoded = encode_base64(special_text)
    print(f"Base64编码: {encoded}")
    decoded = decode_base64(encoded)
    print(f"解码验证: {decoded}")
    
    # 示例4: 多行文本
    multiline_text = """第一行文本
第二行文本
Third line"""
    print(f"\n[示例4] 多行文本:")
    print(multiline_text)
    encoded = encode_base64(multiline_text)
    print(f"Base64编码: {encoded}")
    decoded = decode_base64(encoded)
    print(f"解码验证:\n{decoded}")
    
    # 示例5: 空字符串
    empty_text = ""
    print(f"\n[示例5] 空字符串: '{empty_text}'")
    encoded = encode_base64(empty_text)
    print(f"Base64编码: '{encoded}'")
    
    # 示例6: 错误处理
    print(f"\n[示例6] 错误处理演示:")
    try:
        invalid_input = 12345  # 不支持的类型
        encode_base64(invalid_input)
    except (TypeError, ValueError) as e:
        print(f"错误捕获: {e}")
    
    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)
