"""
Base64 编码/解码功能综合测试模块
测试工程师：base64_tester
功能：全面测试 base64_encoder 和 base64_decoder 模块
"""

import sys
import traceback
from datetime import datetime

# 导入待测试的模块
from base64_encoder import encode_base64
from base64_decoder import decode_base64


class TestResult:
    """测试结果记录类"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.details = []
    
    def add_pass(self, test_name, message=""):
        self.passed += 1
        self.details.append(f"✓ PASS: {test_name} - {message}")
    
    def add_fail(self, test_name, expected, actual, message=""):
        self.failed += 1
        error_msg = f"✗ FAIL: {test_name}\n  期望: {repr(expected)}\n  实际: {repr(actual)}"
        if message:
            error_msg += f"\n  详情: {message}"
        self.errors.append(error_msg)
        self.details.append(error_msg)
    
    def add_error(self, test_name, error):
        self.failed += 1
        error_msg = f"✗ ERROR: {test_name}\n  异常: {str(error)}"
        self.errors.append(error_msg)
        self.details.append(error_msg)
    
    def get_summary(self):
        total = self.passed + self.failed
        return f"\n{'='*60}\n测试总结: 通过 {self.passed}/{total}, 失败 {self.failed}/{total}\n{'='*60}"


def test_normal_strings():
    """测试1: 正常字符串编码解码"""
    result = TestResult()
    test_name = "正常字符串编码解码测试"
    
    test_cases = [
        ("Hello World!", "基本英文字符串"),
        ("Peter", "短英文单词"),
        ("Python is awesome", "带空格句子"),
        ("Test123", "字母数字混合"),
        ("A", "单字符"),
        ("The quick brown fox jumps over the lazy dog", "长句子"),
    ]
    
    for original, description in test_cases:
        try:
            # 编码
            encoded = encode_base64(original)
            # 解码
            decoded = decode_base64(encoded)
            
            # 验证
            if decoded == original:
                result.add_pass(f"{test_name} - {description}", f"'{original}' -> '{encoded}' -> '{decoded}'")
            else:
                result.add_fail(f"{test_name} - {description}", original, decoded, "解码后不匹配")
        except Exception as e:
            result.add_error(f"{test_name} - {description}", e)
    
    return result


def test_special_characters():
    """测试2: 包含特殊字符的字符串"""
    result = TestResult()
    test_name = "特殊字符测试"
    
    test_cases = [
        ("!@#$%^&*()", "特殊符号"),
        ("Test!@#123", "混合特殊字符"),
        ("Hello\nWorld", "换行符"),
        ("Tab\tHere", "制表符"),
        ("Space End ", "末尾空格"),
        (" Special ", "首尾空格"),
        ("Line1\nLine2\nLine3", "多行文本"),
        ("Quote: \"Hello\"", "引号"),
        ("Apostrophe: It's", "撇号"),
        ("Backslash: \\", "反斜杠"),
    ]
    
    for original, description in test_cases:
        try:
            encoded = encode_base64(original)
            decoded = decode_base64(encoded)
            
            if decoded == original:
                result.add_pass(f"{test_name} - {description}", f"'{repr(original)}' 编解码成功")
            else:
                result.add_fail(f"{test_name} - {description}", original, decoded)
        except Exception as e:
            result.add_error(f"{test_name} - {description}", e)
    
    return result


def test_empty_string():
    """测试3: 空字符串"""
    result = TestResult()
    test_name = "空字符串测试"
    
    try:
        original = ""
        encoded = encode_base64(original)
        
        # 空字符串编码后也是空字符串
        if encoded == "":
            result.add_pass(f"{test_name} - 编码", "空字符串编码成功")
        else:
            result.add_fail(f"{test_name} - 编码", "", encoded, "空字符串编码结果不正确")
            
    except Exception as e:
        result.add_error(f"{test_name} - 编码", e)
    
    # 测试空字符串解码（应该抛出异常）
    try:
        decoded = decode_base64("")
        result.add_fail(f"{test_name} - 解码异常处理", "应抛出异常", decoded, "空字符串应该抛出异常")
    except ValueError as e:
        result.add_pass(f"{test_name} - 解码异常处理", f"正确抛出 ValueError: {e}")
    except Exception as e:
        result.add_error(f"{test_name} - 解码异常处理", e)
    
    return result


def test_chinese_characters():
    """测试4: 中文字符"""
    result = TestResult()
    test_name = "中文字符测试"
    
    test_cases = [
        ("你好，世界！", "基本中文问候"),
        ("中文测试", "简单中文"),
        ("Base64编码解码功能测试", "混合中英文字符"),
        ("中华人民共和国", "长中文词组"),
        ("🎉🎊🎁", "Emoji表情"),
        ("日本語テスト", "日文字符"),
        ("한국어 테스트", "韩文字符"),
        ("café naïve résumé", "带重音符号的法语"),
    ]
    
    for original, description in test_cases:
        try:
            encoded = encode_base64(original)
            decoded = decode_base64(encoded)
            
            if decoded == original:
                result.add_pass(f"{test_name} - {description}", f"'{original}' 编解码成功")
            else:
                result.add_fail(f"{test_name} - {description}", original, decoded)
        except Exception as e:
            result.add_error(f"{test_name} - {description}", e)
    
    return result


def test_boundary_cases():
    """测试5: 边界情况"""
    result = TestResult()
    test_name = "边界情况测试"
    
    # 测试1: 超长字符串
    try:
        long_string = "A" * 10000
        encoded = encode_base64(long_string)
        decoded = decode_base64(encoded)
        
        if decoded == long_string:
            result.add_pass(f"{test_name} - 超长字符串(10000字符)", "超长字符串编解码成功")
        else:
            result.add_fail(f"{test_name} - 超长字符串", long_string[:50] + "...", decoded[:50] + "...")
    except Exception as e:
        result.add_error(f"{test_name} - 超长字符串", e)
    
    # 测试2: 仅包含填充需要的字符串
    try:
        for length in [1, 2, 3, 4, 5]:
            original = "x" * length
            encoded = encode_base64(original)
            decoded = decode_base64(encoded)
            
            if decoded == original:
                result.add_pass(f"{test_name} - 长度{length}字符串", f"编码: {encoded}")
            else:
                result.add_fail(f"{test_name} - 长度{length}字符串", original, decoded)
    except Exception as e:
        result.add_error(f"{test_name} - 长度测试", e)
    
    # 测试3: 无效 base64 字符串（应抛出异常）
    invalid_cases = [
        ("!@#$%^&*", "非法字符"),
        ("SGVsbG8gV29ybGQh===", "过多填充"),
        ("SGVsbG8gV29ybGQh", "有效但带空格"),
    ]
    
    for invalid_str, description in invalid_cases:
        try:
            if description == "有效但带空格":
                # 这个应该成功
                decoded = decode_base64("  " + invalid_str + "  ")
                result.add_pass(f"{test_name} - {description}", "带空格字符串处理成功")
            else:
                decoded = decode_base64(invalid_str)
                result.add_fail(f"{test_name} - {description}", "应抛出异常", decoded)
        except ValueError:
            result.add_pass(f"{test_name} - {description}", "正确抛出 ValueError")
        except Exception as e:
            result.add_error(f"{test_name} - {description}", e)
    
    return result


def test_type_validation():
    """测试6: 类型验证"""
    result = TestResult()
    test_name = "类型验证测试"
    
    # 测试编码器类型验证
    invalid_inputs = [
        (123, "整数"),
        (["list"], "列表"),
        ({"key": "value"}, "字典"),
        (None, "None"),
        (3.14, "浮点数"),
        (b"bytes", "字节串"),
    ]
    
    for invalid_input, description in invalid_inputs:
        try:
            encoded = encode_base64(invalid_input)
            result.add_fail(f"{test_name} - 编码器{description}", "应抛出 TypeError", encoded)
        except TypeError:
            result.add_pass(f"{test_name} - 编码器{description}", "正确抛出 TypeError")
        except Exception as e:
            result.add_error(f"{test_name} - 编码器{description}", e)
    
    # 测试解码器类型验证
    for invalid_input, description in invalid_inputs:
        try:
            decoded = decode_base64(invalid_input)
            result.add_fail(f"{test_name} - 解码器{description}", "应抛出 TypeError", decoded)
        except TypeError:
            result.add_pass(f"{test_name} - 解码器{description}", "正确抛出 TypeError")
        except Exception as e:
            result.add_error(f"{test_name} - 解码器{description}", e)
    
    return result


def test_round_trip():
    """测试7: 往返测试（编码后解码）"""
    result = TestResult()
    test_name = "往返一致性测试"
    
    test_strings = [
        "Hello World!",
        "你好，世界！",
        "Test!@#123",
        "A",
        "The quick brown fox jumps over the lazy dog",
        "🎉 Emoji测试 🎊",
        "Mixed: 中文 + English + 123!@#",
        "\n\t\r\n特殊空白字符",
    ]
    
    all_passed = True
    for original in test_strings:
        try:
            encoded = encode_base64(original)
            decoded = decode_base64(encoded)
            
            if decoded == original:
                result.add_pass(f"{test_name} - '{original[:30]}...'" if len(original) > 30 else f"{test_name} - '{original}'")
            else:
                result.add_fail(f"{test_name}", original, decoded, "往返不一致")
                all_passed = False
        except Exception as e:
            result.add_error(f"{test_name}", e)
            all_passed = False
    
    return result


def run_all_tests():
    """运行所有测试并生成报告"""
    print("\n" + "=" * 70)
    print(" " * 15 + "Base64 编码/解码功能测试报告")
    print("=" * 70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试模块: base64_encoder.py, base64_decoder.py")
    print("=" * 70 + "\n")
    
    all_results = []
    
    # 执行所有测试
    test_functions = [
        ("测试1", "正常字符串编码解码", test_normal_strings),
        ("测试2", "特殊字符测试", test_special_characters),
        ("测试3", "空字符串测试", test_empty_string),
        ("测试4", "中文字符测试", test_chinese_characters),
        ("测试5", "边界情况测试", test_boundary_cases),
        ("测试6", "类型验证测试", test_type_validation),
        ("测试7", "往返一致性测试", test_round_trip),
    ]
    
    for test_num, test_desc, test_func in test_functions:
        print(f"\n{'='*70}")
        print(f"{test_num}: {test_desc}")
        print("=" * 70)
        
        result = test_func()
        all_results.append((test_num, test_desc, result))
        
        # 打印详细结果
        for detail in result.details:
            print(detail)
    
    # 生成总结报告
    print("\n" + "=" * 70)
    print(" " * 25 + "最终测试总结")
    print("=" * 70)
    
    total_passed = 0
    total_failed = 0
    
    for test_num, test_desc, result in all_results:
        total_passed += result.passed
        total_failed += result.failed
        status = "✓ PASS" if result.failed == 0 else "✗ FAIL"
        print(f"{test_num}: {test_desc:30s} - 通过: {result.passed:3d}, 失败: {result.failed:3d} [{status}]")
    
    total = total_passed + total_failed
    print("\n" + "=" * 70)
    print(f"总计: 通过 {total_passed}/{total}, 失败 {total_failed}/{total}")
    
    if total_failed == 0:
        print("\n🎉 所有测试通过！编码解码功能正常工作。")
    else:
        print(f"\n⚠️  有 {total_failed} 个测试失败，请检查功能实现。")
    
    print("=" * 70 + "\n")
    
    # 保存测试报告到文件
    save_report(all_results, total_passed, total_failed)
    
    return total_failed == 0


def save_report(all_results, total_passed, total_failed):
    """保存测试报告到文件"""
    report_path = "/home/peter/project/agnet-demo/test_report.txt"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write(" " * 15 + "Base64 编码/解码功能测试报告\n")
        f.write("=" * 70 + "\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试模块: base64_encoder.py, base64_decoder.py\n")
        f.write("=" * 70 + "\n\n")
        
        for test_num, test_desc, result in all_results:
            f.write(f"\n{'='*70}\n")
            f.write(f"{test_num}: {test_desc}\n")
            f.write("=" * 70 + "\n")
            for detail in result.details:
                f.write(detail + "\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write(" " * 25 + "最终测试总结\n")
        f.write("=" * 70 + "\n")
        
        for test_num, test_desc, result in all_results:
            status = "PASS" if result.failed == 0 else "FAIL"
            f.write(f"{test_num}: {test_desc:30s} - 通过: {result.passed:3d}, 失败: {result.failed:3d} [{status}]\n")
        
        total = total_passed + total_failed
        f.write("\n" + "=" * 70 + "\n")
        f.write(f"总计: 通过 {total_passed}/{total}, 失败 {total_failed}/{total}\n")
        
        if total_failed == 0:
            f.write("\n所有测试通过！编码解码功能正常工作。\n")
        else:
            f.write(f"\n有 {total_failed} 个测试失败，请检查功能实现。\n")
        
        f.write("=" * 70 + "\n")
    
    print(f"测试报告已保存至: {report_path}")


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
