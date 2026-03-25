"""
Base64 Demo 验证测试

本测试文件用于验证 base64_encoder_demo 和 base64_decoder_demo 的
一致性和正确性。
"""

import unittest
import sys
import os

# 添加项目目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base64_encoder_demo import encode_base64
from base64_decoder_demo import decode_base64


class TestBase64EncodingDecoding(unittest.TestCase):
    """测试编码和解码的互逆性"""
    
    def test_english_text(self):
        """测试英文文本的编码和解码"""
        test_cases = [
            "Hello, World!",
            "The quick brown fox jumps over the lazy dog",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "abcdefghijklmnopqrstuvwxyz",
            "Python is awesome!",
        ]
        for text in test_cases:
            with self.subTest(text=text):
                encoded = encode_base64(text)
                decoded = decode_base64(encoded)
                self.assertEqual(decoded, text, f"英文文本 '{text}' 编解码失败")
    
    def test_chinese_text(self):
        """测试中文文本的编码和解码"""
        test_cases = [
            "你好，世界！",
            "这是一个测试",
            "Python编程语言",
            "中文字符：你好",
            "混合中英文：Hello 你好 World 世界",
        ]
        for text in test_cases:
            with self.subTest(text=text):
                encoded = encode_base64(text)
                decoded = decode_base64(encoded)
                self.assertEqual(decoded, text, f"中文文本 '{text}' 编解码失败")
    
    def test_numbers(self):
        """测试数字字符串的编码和解码"""
        test_cases = [
            "1234567890",
            "0",
            "9876543210",
            "3.1415926",
            "2024",
        ]
        for text in test_cases:
            with self.subTest(text=text):
                encoded = encode_base64(text)
                decoded = decode_base64(encoded)
                self.assertEqual(decoded, text, f"数字文本 '{text}' 编解码失败")
    
    def test_special_characters(self):
        """测试特殊字符的编码和解码"""
        test_cases = [
            "!@#$%^&*()",
            "[]{}|;':\",./<>?",
            "+-*/=",
            "★☆✓",
            "emoji: 😀🎉🚀",
        ]
        for text in test_cases:
            with self.subTest(text=text):
                encoded = encode_base64(text)
                decoded = decode_base64(encoded)
                self.assertEqual(decoded, text, f"特殊字符 '{text}' 编解码失败")
    
    def test_empty_string(self):
        """测试空字符串"""
        text = ""
        encoded = encode_base64(text)
        # 空字符串编码后也是空
        self.assertIsNotNone(encoded)
        
    def test_mixed_content(self):
        """测试混合内容"""
        test_cases = [
            "Hello 你好 123!",
            "Test@test.com",
            "URL: https://example.com/path?query=1",
            "JSON: {\"name\":\"测试\",\"value\":123}",
        ]
        for text in test_cases:
            with self.subTest(text=text):
                encoded = encode_base64(text)
                decoded = decode_base64(encoded)
                self.assertEqual(decoded, text, f"混合内容 '{text}' 编解码失败")
    
    def test_multiline_text(self):
        """测试多行文本"""
        test_cases = [
            "第一行\n第二行\n第三行",
            "Line 1\nLine 2",
            "Paragraph 1\n\nParagraph 2",
        ]
        for text in test_cases:
            with self.subTest(text=text):
                encoded = encode_base64(text)
                decoded = decode_base64(encoded)
                self.assertEqual(decoded, text, f"多行文本编解码失败")
    
    def test_long_text(self):
        """测试长文本"""
        text = "A" * 1000
        encoded = encode_base64(text)
        decoded = decode_base64(encoded)
        self.assertEqual(decoded, text, "长文本编解码失败")


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""
    
    def test_decode_invalid_base64(self):
        """测试解码无效的base64字符串"""
        # 这些输入应该会导致解码错误
        # - 包含非ASCII字符（非UTF-8字节序列解码后）
        # - 填充错误
        # - 格式错误的base64
        invalid_cases = [
            "abc!",     # 非标准填充
            "abc==xyz", # 填充后还有字符
        ]
        for invalid in invalid_cases:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    decode_base64(invalid)
    
    def test_decode_none(self):
        """测试解码None"""
        with self.assertRaises(ValueError):
            decode_base64(None)
    
    def test_encode_invalid_type(self):
        """测试编码无效类型"""
        invalid_inputs = [
            12345,
            3.14,
            ["list"],
            {"key": "value"},
        ]
        for invalid in invalid_inputs:
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    encode_base64(invalid)
    
    def test_decode_empty_string(self):
        """测试解码空字符串"""
        # decoder demo中的decode_base64对空字符串会抛出ValueError
        with self.assertRaises(ValueError):
            decode_base64("")


class TestCrossCompatibility(unittest.TestCase):
    """测试两个模块的兼容性"""
    
    def test_encoder_can_decode(self):
        """测试encoder模块的decode功能"""
        from base64_encoder_demo import decode_base64 as encoder_decode
        
        text = "测试encoder的解码功能"
        encoded = encode_base64(text)
        decoded = encoder_decode(encoded)
        self.assertEqual(decoded, text)
    
    def test_cross_module_compatibility(self):
        """测试跨模块编解码兼容性"""
        from base64_encoder_demo import decode_base64 as encoder_decode
        from base64_decoder_demo import decode_base64 as decoder_decode
        
        text = "跨模块测试文本"
        encoded = encode_base64(text)
        
        # 使用decoder模块解码
        decoded1 = decoder_decode(encoded)
        # 使用encoder模块的decode功能解码
        decoded2 = encoder_decode(encoded)
        
        self.assertEqual(decoded1, text)
        self.assertEqual(decoded2, text)
        self.assertEqual(decoded1, decoded2)


class TestBase64Standards(unittest.TestCase):
    """测试是否符合base64标准"""
    
    def test_standard_base64_alphabet(self):
        """测试编码结果只包含标准base64字符"""
        import base64 as std_base64
        
        text = "Hello, World! 你好"
        encoded = encode_base64(text)
        
        # 验证只包含base64标准字符
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
        for char in encoded:
            self.assertIn(char, valid_chars, f"编码结果包含非法字符: {char}")
    
    def test_against_standard_library(self):
        """与Python标准库对比"""
        import base64 as std_base64
        
        test_cases = [
            "Hello, World!",
            "你好，世界！",
            "Test 123",
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                # 我们的编码
                our_encoded = encode_base64(text)
                # 标准库的编码
                std_encoded = std_base64.b64encode(text.encode('utf-8')).decode('ascii')
                
                self.assertEqual(our_encoded, std_encoded, 
                    f"编码结果与标准库不一致: {text}")
                
                # 我们的解码
                our_decoded = decode_base64(std_encoded)
                self.assertEqual(our_decoded, text, 
                    f"解码结果与原始文本不一致: {text}")


def run_tests():
    """运行所有测试并生成报告"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestBase64EncodingDecoding))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestCrossCompatibility))
    suite.addTests(loader.loadTestsFromTestCase(TestBase64Standards))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 生成测试报告
    print("\n" + "=" * 70)
    print("测试报告")
    print("=" * 70)
    print(f"测试总数: {result.testsRun}")
    print(f"通过数量: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败数量: {len(result.failures)}")
    print(f"错误数量: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, trace in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n出错的测试:")
        for test, trace in result.errors:
            print(f"  - {test}")
    
    print("\n" + "=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
