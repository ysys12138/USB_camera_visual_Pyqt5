#!/usr/bin/env python3
"""
测试服务层
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.activation_service import ActivationService


def test_activation_service():
    print("=== 测试激活服务 ===")

    # 1. 创建服务实例
    service = ActivationService()
    print("1. 服务初始化完成")

    # 2. 检查初始状态
    activated, info = service.check_activation_status()
    print(f"2. 初始状态: {'已激活' if activated else '未激活'}")

    # 3. 生成测试激活码
    test_key = service.generate_license_key()
    print(f"3. 生成的测试激活码: {test_key}")

    # 4. 验证格式
    is_valid, message = service.validate_license_format(test_key)
    print(f"4. 格式验证: {is_valid} - {message}")

    # 5. 尝试激活
    if not activated:
        print("\n5. 尝试激活软件...")
        success, msg = service.activate_software(test_key)
        print(f"   激活结果: {success} - {msg}")

        # 6. 再次检查状态
        activated, info = service.check_activation_status()
        print(f"6. 激活后状态: {'已激活' if activated else '未激活'}")

        if activated:
            print(f"   激活信息: {info}")

    # 7. 测试重复激活
    print("\n7. 测试重复激活...")
    success, msg = service.activate_software(test_key)  # 相同的激活码
    print(f"   结果: {success} - {msg} (应该失败)")

    # 8. 生成批量测试码
    print("\n8. 生成批量测试码:")
    batch_keys = service.generate_test_keys(3)
    for i, key in enumerate(batch_keys, 1):
        print(f"   {i}. {key}")

    # 9. 测试错误格式
    print("\n9. 测试错误格式:")
    test_cases = [
        "ABCD",  # 太短
        "ABCD-EFGH-IJKL-MNOP-XYZ",  # 太长
        "1234-5678-90AB-CDEF",  # 包含0,1
    ]

    for key in test_cases:
        is_valid, msg = service.validate_license_format(key)
        print(f"   '{key}': {is_valid} - {msg}")

    # 10. 获取使用统计
    print(f"\n10. 已使用的激活码数量: {service.get_used_keys_count()}")

    # 11. 重置测试（可选）
    print("\n11. 重置激活状态...")
    if service.reset_activation():
        print("   重置成功")
        activated, _ = service.check_activation_status()
        print(f"   重置后状态: {'已激活' if activated else '未激活'}")


def main():
    print("🧪 测试服务层\n")
    test_activation_service()
    print("\n✅ 服务层测试完成")


if __name__ == "__main__":
    main()