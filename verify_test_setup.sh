#!/bin/bash

echo "========================================="
echo "测试环境配置验证"
echo "========================================="
echo ""

# 检查所有必需文件
echo "1. 检查测试框架文件..."
files=(
    "backend/tests/conftest.py"
    "backend/tests/test_api/test_auth.py"
    "backend/tests/test_opencode_sidecar.py"
    "backend/tests/fixtures/users.py"
    "backend/pytest.ini"
    "backend/requirements-test.txt"
    "docs/testing/README.md"
    ".github/workflows/test.yml"
)

all_found=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (缺失)"
        all_found=false
    fi
done

echo ""
echo "2. 检查测试依赖安装..."
cd backend
python3 -m pytest --version > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ pytest已安装"
else
    echo "❌ pytest未安装"
    all_found=false
fi

echo ""
echo "3. 检查测试收集..."
python3 -m pytest --collect-only -q > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 测试可以正常收集"
    test_count=$(python3 -m pytest --collect-only -q | grep "test session starts" -A 1000 | grep -c "Coroutine\|Function")
    echo "   发现 $test_count 个测试"
else
    echo "❌ 测试收集失败"
    all_found=false
fi

echo ""
echo "========================================="
if [ "$all_found" = true ]; then
    echo "✅ 所有检查通过！测试环境配置完成。"
else
    echo "⚠️  部分检查失败，请查看上述详情。"
fi
echo "========================================="
