-- Skills Hub 数据库架构
-- Sprint 11: 技能发布和包管理

-- 已发布技能表
CREATE TABLE IF NOT EXISTS published_skills (
    id SERIAL PRIMARY KEY,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    publisher_id INTEGER NOT NULL REFERENCES users(id),
    
    -- 基本信息
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE,
    description TEXT,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    
    -- 分类和标签
    category VARCHAR(50),
    tags JSONB,
    
    -- 定价信息
    price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    
    -- 发布状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, published, rejected, deprecated
    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- 统计信息
    download_count INTEGER NOT NULL DEFAULT 0,
    install_count INTEGER NOT NULL DEFAULT 0,
    rating NUMERIC(3, 2) NOT NULL DEFAULT 0.00,
    rating_count INTEGER NOT NULL DEFAULT 0,
    
    -- 元数据
    homepage_url VARCHAR(500),
    repository_url VARCHAR(500),
    documentation_url VARCHAR(500),
    license VARCHAR(50) NOT NULL DEFAULT 'MIT',
    
    -- 时间戳
    published_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_published_skills_skill_id ON published_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_published_skills_publisher_id ON published_skills(publisher_id);
CREATE INDEX IF NOT EXISTS idx_published_skills_name ON published_skills(name);
CREATE INDEX IF NOT EXISTS idx_published_skills_slug ON published_skills(slug);
CREATE INDEX IF NOT EXISTS idx_published_skills_category ON published_skills(category);
CREATE INDEX IF NOT EXISTS idx_published_skills_status ON published_skills(status);
CREATE INDEX IF NOT EXISTS idx_published_skills_download_count ON published_skills(download_count DESC);
CREATE INDEX IF NOT EXISTS idx_published_skills_rating ON published_skills(rating DESC);

-- 技能包表
CREATE TABLE IF NOT EXISTS skill_packages (
    id SERIAL PRIMARY KEY,
    published_skill_id INTEGER NOT NULL REFERENCES published_skills(id) ON DELETE CASCADE,
    
    -- 版本信息
    version VARCHAR(20) NOT NULL,
    version_code INTEGER NOT NULL DEFAULT 1,
    
    -- 存储信息
    storage_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    
    -- 依赖信息
    dependencies JSONB,
    min_platform_version VARCHAR(20),
    
    -- 发布说明
    release_notes TEXT,
    changelog TEXT,
    
    -- 状态
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_latest BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- 统计
    download_count INTEGER NOT NULL DEFAULT 0,
    
    -- 时间戳
    published_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束
    UNIQUE(published_skill_id, version)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_skill_packages_published_skill_id ON skill_packages(published_skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_packages_version ON skill_packages(version);
CREATE INDEX IF NOT EXISTS idx_skill_packages_version_code ON skill_packages(version_code);
CREATE INDEX IF NOT EXISTS idx_skill_packages_is_latest ON skill_packages(is_latest) WHERE is_latest = TRUE;

-- 技能权限表
CREATE TABLE IF NOT EXISTS skill_permissions (
    id SERIAL PRIMARY KEY,
    published_skill_id INTEGER NOT NULL REFERENCES published_skills(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 权限类型
    permission_type VARCHAR(20) NOT NULL,  -- owner, admin, write, read
    granted_by INTEGER REFERENCES users(id),
    
    -- 时间戳
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- 唯一约束
    UNIQUE(published_skill_id, user_id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_skill_permissions_published_skill_id ON skill_permissions(published_skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_permissions_user_id ON skill_permissions(user_id);

-- 技能评价表
CREATE TABLE IF NOT EXISTS skill_reviews (
    id SERIAL PRIMARY KEY,
    published_skill_id INTEGER NOT NULL REFERENCES published_skills(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- 评价内容
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200),
    content TEXT,
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束（每个用户只能评价一次）
    UNIQUE(published_skill_id, user_id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_skill_reviews_published_skill_id ON skill_reviews(published_skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_reviews_user_id ON skill_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_skill_reviews_rating ON skill_reviews(rating);

-- 触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_published_skills_updated_at
    BEFORE UPDATE ON published_skills
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_skill_reviews_updated_at
    BEFORE UPDATE ON skill_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
