"""
Skill 模型字段测试

测试新增的 Skill 模型字段：prompt_template, category, slug, use_count
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.skill import Skill
from app.core.security import get_password_hash


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """创建测试用户"""
    user = User(
        email="skilltest@example.com",
        username="skilltestuser",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_skill_model_has_prompt_template_field(db_session: AsyncSession, test_user: User):
    """测试 Skill 模型包含 prompt_template 字段"""
    skill = Skill(
        user_id=test_user.id,
        name="Test Skill",
        prompt_template="You are a helpful assistant. Please help with: {query}",
        skill_type="custom"
    )
    db_session.add(skill)
    await db_session.commit()
    await db_session.refresh(skill)
    
    # 验证字段存在且可以保存
    assert skill.prompt_template == "You are a helpful assistant. Please help with: {query}"
    assert skill.id is not None


@pytest.mark.asyncio
async def test_skill_model_has_category_field(db_session: AsyncSession, test_user: User):
    """测试 Skill 模型包含 category 字段"""
    skill = Skill(
        user_id=test_user.id,
        name="Test Skill",
        category="AI Assistant",
        skill_type="custom"
    )
    db_session.add(skill)
    await db_session.commit()
    await db_session.refresh(skill)
    
    # 验证字段存在且可以保存
    assert skill.category == "AI Assistant"
    assert skill.id is not None


@pytest.mark.asyncio
async def test_skill_model_has_slug_field(db_session: AsyncSession, test_user: User):
    """测试 Skill 模型包含 slug 字段"""
    skill = Skill(
        user_id=test_user.id,
        name="Test Skill",
        slug="test-skill-unique-slug",
        skill_type="custom"
    )
    db_session.add(skill)
    await db_session.commit()
    await db_session.refresh(skill)
    
    # 验证字段存在且可以保存
    assert skill.slug == "test-skill-unique-slug"
    assert skill.id is not None


@pytest.mark.asyncio
async def test_skill_model_slug_unique_constraint(db_session: AsyncSession, test_user: User):
    """测试 Skill 模型的 slug 字段唯一性约束"""
    # 创建第一个技能
    skill1 = Skill(
        user_id=test_user.id,
        name="Skill 1",
        slug="unique-test-slug",
        skill_type="custom"
    )
    db_session.add(skill1)
    await db_session.commit()
    
    # 尝试创建第二个具有相同 slug 的技能
    skill2 = Skill(
        user_id=test_user.id,
        name="Skill 2",
        slug="unique-test-slug",  # 重复的 slug
        skill_type="custom"
    )
    db_session.add(skill2)
    
    # 应该抛出 IntegrityError
    with pytest.raises(Exception):  # SQLAlchemy IntegrityError
        await db_session.commit()


@pytest.mark.asyncio
async def test_skill_model_has_use_count_field(db_session: AsyncSession, test_user: User):
    """测试 Skill 模型包含 use_count 字段"""
    skill = Skill(
        user_id=test_user.id,
        name="Test Skill",
        skill_type="custom"
    )
    db_session.add(skill)
    await db_session.commit()
    await db_session.refresh(skill)
    
    # 验证字段存在且默认值为 0
    assert skill.use_count == 0
    assert skill.id is not None
    
    # 增加使用次数
    skill.use_count += 1
    await db_session.commit()
    await db_session.refresh(skill)
    
    assert skill.use_count == 1


@pytest.mark.asyncio
async def test_skill_model_all_new_fields_together(db_session: AsyncSession, test_user: User):
    """测试所有新字段可以一起使用"""
    skill = Skill(
        user_id=test_user.id,
        name="Complete Test Skill",
        prompt_template="Template with {var1} and {var2}",
        category="Testing",
        slug="complete-test-skill",
        use_count=10,
        skill_type="custom"
    )
    db_session.add(skill)
    await db_session.commit()
    await db_session.refresh(skill)
    
    # 验证所有字段
    assert skill.prompt_template == "Template with {var1} and {var2}"
    assert skill.category == "Testing"
    assert skill.slug == "complete-test-skill"
    assert skill.use_count == 10


@pytest.mark.asyncio
async def test_skill_model_nullable_fields(db_session: AsyncSession, test_user: User):
    """测试可选字段可以为 None"""
    skill = Skill(
        user_id=test_user.id,
        name="Minimal Skill",
        prompt_template=None,
        category=None,
        slug=None,
        skill_type="custom"
    )
    db_session.add(skill)
    await db_session.commit()
    await db_session.refresh(skill)
    
    # 验证可选字段可以为 None
    assert skill.prompt_template is None
    assert skill.category is None
    assert skill.slug is None
    # use_count 应该有默认值
    assert skill.use_count == 0


@pytest.mark.asyncio
async def test_skill_model_query_by_category(db_session: AsyncSession, test_user: User):
    """测试通过 category 字段查询技能"""
    # 创建不同类别的技能
    skill1 = Skill(
        user_id=test_user.id,
        name="AI Skill 1",
        category="AI",
        skill_type="custom"
    )
    skill2 = Skill(
        user_id=test_user.id,
        name="AI Skill 2",
        category="AI",
        skill_type="custom"
    )
    skill3 = Skill(
        user_id=test_user.id,
        name="Dev Skill",
        category="Development",
        skill_type="custom"
    )
    
    db_session.add_all([skill1, skill2, skill3])
    await db_session.commit()
    
    # 查询 AI 类别的技能
    result = await db_session.execute(
        select(Skill).where(Skill.category == "AI")
    )
    ai_skills = result.scalars().all()
    
    assert len(ai_skills) == 2
    assert all(s.category == "AI" for s in ai_skills)


@pytest.mark.asyncio
async def test_skill_model_query_by_slug(db_session: AsyncSession, test_user: User):
    """测试通过 slug 字段查询技能"""
    skill = Skill(
        user_id=test_user.id,
        name="Slug Test Skill",
        slug="unique-slug-for-query",
        skill_type="custom"
    )
    db_session.add(skill)
    await db_session.commit()
    
    # 通过 slug 查询
    result = await db_session.execute(
        select(Skill).where(Skill.slug == "unique-slug-for-query")
    )
    found_skill = result.scalar_one_or_none()
    
    assert found_skill is not None
    assert found_skill.name == "Slug Test Skill"
    assert found_skill.slug == "unique-slug-for-query"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
