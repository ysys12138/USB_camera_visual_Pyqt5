#!/usr/bin/env python3
"""
测试核心算法
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_config import MASTER_SECRET, LICENSE_CHARSET
from core.activation import LicenseKeyGenerator, ActivationCore
from core.validators import validate_license_format


def test_key_generator():
    """测试激活码生成器"""
    print("=== 测试激活码生成器 ===")

    generator = LicenseKeyGenerator(charset=LICENSE_CHARSET)

    # 1. 生成单个激活码
    key = generator.generate_random_key()
    print(f"1. 生成的激活码: {key}")

    # 2. 验证格式
    is_valid, message = generator.validate_format(key)
    print(f"2. 格式验证: {is_valid} - {message}")

    # 3. 测试错误格式
    invalid_key = "ABCD-EFGH-IJKL-MNOP"
    is_valid, message = generator.validate_format(invalid_key)
    print(f"3. 错误格式测试: {is_valid} - {message}")

    # 4. 测试校验和
    # 修改一个字符，应该验证失败
    modified_key = key[:-1] + ('A' if key[-1] != 'A' else 'B')
    is_valid, message = generator.validate_format(modified_key)
    print(f"4. 篡改测试: {is_valid} - {message}")

    return key


def test_activation_core():
    """测试激活核心"""
    print("\n=== 测试激活核心 ===")

    core = ActivationCore(MASTER_SECRET)

    # 1. 生成激活码
    key = core.generate_license_key()
    print(f"1. 核心生成的激活码: {key}")

    # 2. 验证格式
    is_valid = core.verify_license_key(key)
    print(f"2. 核心验证: {is_valid}")

    # 3. 计算签名
    signature = core.calculate_key_signature(key)
    print(f"3. 激活码签名: {signature[:16]}...")

    # 4. 批量生成
    batch_keys = core.generate_batch_keys(3)
    print(f"4. 批量生成 {len(batch_keys)} 个:")
    for i, k in enumerate(batch_keys, 1):
        print(f"   {i}. {k}")

    # 5. 标准化测试
    test_cases = [
        "abcd1234efgh5678",
        "ABCD 1234 EFGH 5678",
        "abcd-1234-efgh-5678",
        "AbCd-1E3g-HiJk-9M8n"
    ]

    print("5. 标准化测试:")
    for test in test_cases:
        normalized = core.normalize_key(test)
        print(f"   '{test}' -> '{normalized}'")


def test_validators():
    """测试验证工具"""
    print("\n=== 测试验证工具 ===")

    test_cases = [
        ("X7B9-2K4F-H8J3-M5N1", True),
        ("ABCD-EFGH-IJKL-MNOP", True),
        ("1234-5678-90AB-CDEF", True),
        ("ABCDEFGHIJKLMNOP", False),  # 没有分隔符
        ("ABCD-EFGH-IJKL", False),  # 长度不够
    ]

    for key, expected_valid in test_cases:
        is_valid, message = validate_license_format(key)
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"{status} '{key}': {is_valid} - {message or 'OK'}")


def main():
    """主测试函数"""
    print("🧪 测试核心算法层\n")

    # 测试各部分
    test_key_generator()
    test_activation_core()
    test_validators()

    print("\n✅ 核心算法测试完成")


if __name__ == "__main__":
    main()