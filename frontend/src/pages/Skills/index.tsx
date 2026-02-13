import React, { useState } from 'react'
import { Input, Button, Card, Tag, List, Empty, message } from 'antd'
import { SearchOutlined, DownloadOutlined, StarOutlined } from '@ant-design/icons'
import client from '@/api/client'

const { Search } = Input

export default function SkillsPage() {
  const [skills, setSkills] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')

  const searchSkills = async (keyword: string) => {
    setLoading(true)
    try {
      const response = await client.get('/skills', {
        params: { search: keyword }
      })
      setSkills(response.data)
    } catch (error: any) {
      message.error('搜索失败')
    } finally {
      setLoading(false)
    }
  }

  const installSkill = async (skillId: string) => {
    try {
      await client.post(`/skills/${skillId}/install`)
      message.success('安装成功')
    } catch (error: any) {
      message.error('安装失败')
    }
  }

  useEffect(() => {
    searchSkills('')
  }, [])

  return (
    <div style={{ padding: '20px' }}>
      <h2>技能市场</h2>

      <Search
        placeholder="搜索技能"
        allowClear
        enterButton="搜索"
        size="large"
        onSearch={searchSkills}
        style={{ marginBottom: '20px' }}
      />

      {skills.length === 0 ? (
        <Empty description="暂无技能" />
      ) : (
        <List
          grid={{ gutter: 16, column: 3 }}
          dataSource={skills}
          renderItem={(skill: any) => (
            <List.Item>
              <Card
                title={skill.name}
                extra={
                  <Tag color="blue">{skill.category || '通用'}</Tag>
                }
              >
                <p>{skill.description}</p>
                <div style={{ marginBottom: '12px' }}>
                  <Tag icon={<DownloadOutlined />}>{skill.downloads || 0}</Tag>
                  <Tag icon={<StarOutlined />}>{skill.rating_avg?.toFixed(1) || '0.0'}</Tag>
                </div>
                <Button
                  type="primary"
                  block
                  onClick={() => installSkill(skill.id)}
                >
                  安装
                </Button>
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  )
}

// 添加useEffect导入
import { useEffect } from 'react'
