#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base64 解码演示程序

本程序实现了Base64编码字符串的解码功能，支持中文、特殊字符等各种类型的编码文本。
"""

import base64


def decode_base64(encoded_text):
    """
    将Base64编码的字符串解码为原始文本

    参数:
        encoded_text (str): Base64编码的字符串

    返回:
        str: 解码后的原始文本

    异常:
        ValueError: 当输入不是有效的Base64编码时抛出
    """
    # 检查输入是否为None或空字符串
    if encoded_text is None:
        raise ValueError("输入不能为None")
    
    if not encoded_text.strip():
        raise ValueError("输入不能为空字符串")
    
    try:
        # 将字符串转换为bytes（使用UTF-8编码）
        encoded_bytes = encoded_text.encode('utf-8')
        
        # 执行Base64解码
        decoded_bytes = base64.b64decode(encoded_bytes)
        
        # 将解码后的bytes转换为字符串（使用UTF-8编码以支持中文）
        decoded_text = decoded_bytes.decode('utf-8')
        
        return decoded_text
    
    except base64.binascii.Error as e:
        # 处理无效的Base64编码
        raise ValueError(f"无效的Base64编码: {str(e)}")
    
    except UnicodeDecodeError as e:
        # 处理解码后的字节无法转换为UTF-8字符串的情况
        raise ValueError(f"解码后的内容无法转换为UTF-8字符串: {str(e)}")
    
    except Exception as e:
        # 处理其他未知异常
        raise ValueError(f"解码过程中发生错误: {str(e)}")


def main():
    """
    示例代码：展示如何使用decode_base64函数
    """
    print("=" * 50)
    print("Base64 解码演示程序")
    print("=" * 50)
    
    # 示例1: 解码英文文本
    print("\n示例1: 解码英文文本")
    encoded_text_1 = "SGVsbG8gV29ybGQh"
    print(f"Base64编码: {encoded_text_1}")
    try:
        decoded_text_1 = decode_base64(encoded_text_1)
        print(f"解码结果: {decoded_text_1}")
    except ValueError as e:
        print(f"解码失败: {e}")
    
    # 示例2: 解码中文文本
    print("\n示例2: 解码中文文本")
    encoded_text_2 = "5L2g5aW9LCDkuIDkuIDmrKHvvIE="
    print(f"Base64编码: {encoded_text_2}")
    try:
        decoded_text_2 = decode_base64(encoded_text_2)
        print(f"解码结果: {decoded_text_2}")
    except ValueError as e:
        print(f"解码失败: {e}")
    
    # 示例3: 解码包含特殊字符的文本
    print("\n示例3: 解码包含特殊字符的文本")
    encoded_text_3 = "SGVsbG8gQCNfJCYrPCE+Py8oKVtd"
    print(f"Base64编码: {encoded_text_3}")
    try:
        decoded_text_3 = decode_base64(encoded_text_3)
        print(f"解码结果: {decoded_text_3}")
    except ValueError as e:
        print(f"解码失败: {e}")
    
    # 示例4: 错误处理演示 - 无效的Base64编码
    print("\n示例4: 错误处理演示 - 无效的Base64编码")
    invalid_encoded_text = "ThisIsNotValidBase64!!!"
    print(f"Base64编码: {invalid_encoded_text}")
    try:
        decoded_text_invalid = decode_base64(invalid_encoded_text)
        print(f"解码结果: {decoded_text_invalid}")
    except ValueError as e:
        print(f"解码失败: {e}")
    
    print("\n" + "=" * 50)
    print("演示完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
