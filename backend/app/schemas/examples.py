"""
API文档示例

为OpenAPI/Swagger文档提供详细的请求和响应示例
"""

# 认证相关示例
AUTH_EXAMPLES = {
    "login_request": {
        "summary": "用户登录",
        "description": "使用邮箱和密码登录",
        "value": {
            "email": "user@example.com",
            "password": "securepassword123"
        }
    },
    "login_response_success": {
        "summary": "登录成功",
        "value": {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": 1,
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False
            }
        }
    },
    "register_request": {
        "summary": "用户注册",
        "value": {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepassword123",
            "full_name": "New User"
        }
    }
}

# 用户相关示例
USER_EXAMPLES = {
    "user_response": {
        "summary": "用户信息",
        "value": {
            "id": 1,
            "email": "user@example.com",
            "username": "johndoe",
            "full_name": "John Doe",
            "avatar_url": "https://example.com/avatar.jpg",
            "bio": "Software developer",
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
            "permissions": ["create_skills", "execute_skills"],
            "roles": ["developer"],
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-20T14:22:00Z"
        }
    },
    "user_update_request": {
        "summary": "更新用户信息",
        "value": {
            "full_name": "John Updated",
            "bio": "Senior Software Developer",
            "avatar_url": "https://example.com/new-avatar.jpg"
        }
    }
}

# 技能相关示例
SKILL_EXAMPLES = {
    "skill_create_request": {
        "summary": "创建技能",
        "value": {
            "name": "Code Reviewer",
            "description": "AI-powered code review skill that analyzes code quality and suggests improvements",
            "category": "development",
            "prompt_template": "Please review the following code and provide feedback:\n\n{code}\n\nFocus on: {focus_areas}",
            "config": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "tags": ["code-review", "quality", "ai"],
            "is_public": True
        }
    },
    "skill_response": {
        "summary": "技能详情",
        "value": {
            "id": 1,
            "user_id": 1,
            "name": "Code Reviewer",
            "slug": "code-reviewer",
            "description": "AI-powered code review skill",
            "category": "development",
            "prompt_template": "Please review the following code...",
            "config": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "tags": ["code-review", "quality", "ai"],
            "is_public": True,
            "is_active": True,
            "use_count": 150,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-20T14:22:00Z",
            "user": {
                "id": 1,
                "username": "johndoe",
                "full_name": "John Doe"
            }
        }
    },
    "skill_list_response": {
        "summary": "技能列表",
        "value": {
            "items": [
                {
                    "id": 1,
                    "name": "Code Reviewer",
                    "slug": "code-reviewer",
                    "description": "AI-powered code review",
                    "category": "development",
                    "tags": ["code-review", "ai"],
                    "use_count": 150,
                    "created_at": "2024-01-15T10:30:00Z"
                },
                {
                    "id": 2,
                    "name": "Documentation Generator",
                    "slug": "doc-generator",
                    "description": "Auto-generate documentation",
                    "category": "documentation",
                    "tags": ["docs", "automation"],
                    "use_count": 89,
                    "created_at": "2024-01-16T12:15:00Z"
                }
            ],
            "total": 2,
            "page": 1,
            "page_size": 20,
            "has_more": False
        }
    },
    "skill_execution_request": {
        "summary": "执行技能",
        "value": {
            "input_params": {
                "code": "def hello_world():\n    print('Hello, World!')",
                "focus_areas": ["style", "performance", "best-practices"]
            },
            "async_mode": False
        }
    },
    "skill_execution_response": {
        "summary": "执行结果",
        "value": {
            "execution_id": "exec-12345",
            "skill_id": 1,
            "status": "success",
            "output_result": {
                "feedback": [
                    {
                        "line": 1,
                        "type": "style",
                        "message": "Consider adding type hints"
                    },
                    {
                        "line": 2,
                        "type": "best-practices",
                        "message": "Use logging instead of print for production code"
                    }
                ],
                "score": 85,
                "summary": "Code is functional but could benefit from type hints and logging"
            },
            "execution_time": 2340,
            "started_at": "2024-01-20T14:22:00Z",
            "completed_at": "2024-01-20T14:22:02Z"
        }
    }
}

# 会话相关示例
SESSION_EXAMPLES = {
    "session_create_request": {
        "summary": "创建会话",
        "value": {
            "title": "Python Development Session",
            "description": "Working on a Python web scraper project",
            "model_name": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
            "context": {
                "project_type": "web-scraper",
                "language": "python"
            }
        }
    },
    "session_response": {
        "summary": "会话详情",
        "value": {
            "id": 1,
            "user_id": 1,
            "title": "Python Development Session",
            "description": "Working on a Python web scraper",
            "status": "running",
            "model_name": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
            "total_messages": 25,
            "total_tokens": 5420,
            "created_at": "2024-01-20T14:00:00Z",
            "updated_at": "2024-01-20T14:22:00Z",
            "started_at": "2024-01-20T14:00:05Z"
        }
    },
    "message_request": {
        "summary": "发送消息",
        "value": {
            "content": "Can you help me write a function to scrape product prices from an e-commerce website?",
            "role": "user"
        }
    },
    "message_response": {
        "summary": "AI响应",
        "value": {
            "id": "msg-12345",
            "session_id": 1,
            "role": "assistant",
            "content": "I'd be happy to help you write a web scraping function! Here's a basic example using Python and BeautifulSoup...",
            "tokens": 150,
            "created_at": "2024-01-20T14:22:30Z"
        }
    }
}

# 文件相关示例
FILE_EXAMPLES = {
    "file_list_response": {
        "summary": "文件列表",
        "value": {
            "items": [
                {
                    "id": 1,
                    "filename": "project.py",
                    "file_path": "/projects/scraper/project.py",
                    "file_type": "python",
                    "size": 4096,
                    "created_at": "2024-01-20T14:00:00Z",
                    "updated_at": "2024-01-20T14:22:00Z"
                },
                {
                    "id": 2,
                    "filename": "config.json",
                    "file_path": "/projects/scraper/config.json",
                    "file_type": "json",
                    "size": 512,
                    "created_at": "2024-01-20T14:05:00Z",
                    "updated_at": "2024-01-20T14:05:00Z"
                }
            ],
            "total": 2
        }
    }
}

# 错误响应示例
ERROR_EXAMPLES = {
    "validation_error": {
        "summary": "验证错误",
        "value": {
            "error": {
                "code": "ERR_1002",
                "message": "Validation failed",
                "details": {
                    "validation_errors": [
                        {
                            "field": "email",
                            "message": "Invalid email format",
                            "type": "value_error.email"
                        }
                    ]
                }
            }
        }
    },
    "unauthorized_error": {
        "summary": "未授权",
        "value": {
            "error": {
                "code": "ERR_2000",
                "message": "Authentication required",
                "details": {}
            }
        }
    },
    "not_found_error": {
        "summary": "资源未找到",
        "value": {
            "error": {
                "code": "ERR_3000",
                "message": "Requested resource not found",
                "details": {
                    "resource_type": "Skill",
                    "resource_id": 999
                }
            }
        }
    },
    "rate_limit_error": {
        "summary": "频率限制",
        "value": {
            "error": {
                "code": "ERR_1003",
                "message": "Too many requests. Please try again later",
                "details": {
                    "limit": 60,
                    "window": "1 minute",
                    "retry_after": 45
                }
            }
        }
    }
}

# 导出所有示例
ALL_EXAMPLES = {
    "auth": AUTH_EXAMPLES,
    "user": USER_EXAMPLES,
    "skill": SKILL_EXAMPLES,
    "session": SESSION_EXAMPLES,
    "file": FILE_EXAMPLES,
    "error": ERROR_EXAMPLES
}
