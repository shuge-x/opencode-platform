import React, { useState, useEffect } from 'react'
import {
  Input,
  Select,
  Card,
  Tag,
  List,
  Empty,
  Pagination,
  Spin,
  Radio,
  Row,
  Col,
  Affix,
  Drawer,
  Button,
  Rate,
  message,
  AutoComplete,
} from 'antd'
import {
  SearchOutlined,
  DownloadOutlined,
  StarOutlined,
  AppstoreOutlined,
  BarsOutlined,
  FilterOutlined,
  StarFilled,
} from '@ant-design/icons'
import { useDebounce } from 'lodash-es'
import { useSkillSearch, useSkillCategories, useSkillSuggestions, useInstallSkill } from '@/hooks/useSkillSearch'
import type { PublishedSkill } from '@/api/skillSearch'
import './SearchPage.css'

const { Search } = Input
const { Option } = Select

type ViewMode = 'grid' | 'list'
type PriceFilter = 'all' | 'free' | 'paid'
type SortBy = 'latest' | 'popular' | 'rating'

export default function SkillSearchPage() {
  // 搜索状态
  const [searchKeyword, setSearchKeyword] = useState('')
  const [debouncedKeyword, setDebouncedKeyword] = useState('')
  const [category, setCategory] = useState<string | undefined>()
  const [priceFilter, setPriceFilter] = useState<PriceFilter>('all')
  const [minRating, setMinRating] = useState<number | undefined>()
  const [sortBy, setSortBy] = useState<SortBy>('popular')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(12)
  
  // UI状态
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  
  // 防抖搜索
  const debouncedSearch = useDebounce((value: string) => {
    setDebouncedKeyword(value)
    setPage(1)
  }, 300)
  
  // 搜索建议
  const { data: suggestionsData, isLoading: suggestionsLoading } = useSkillSuggestions(
    searchKeyword,
    searchKeyword.length >= 2
  )
  
  useEffect(() => {
    if (suggestionsData) {
      setSuggestions(suggestionsData)
    }
  }, [suggestionsData])
  
  // 查询
  const { data, isLoading, isError } = useSkillSearch({
    search: debouncedKeyword || undefined,
    category: category && category !== '全部' ? category : undefined,
    min_rating: minRating,
    price_filter: priceFilter,
    sort_by: sortBy,
    page,
    page_size: pageSize,
  })
  
  const { data: categories } = useSkillCategories()
  const installSkill = useInstallSkill()
  
  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchKeyword(value)
    debouncedSearch(value)
  }
  
  // 处理分类选择
  const handleCategoryChange = (cat: string) => {
    setCategory(cat)
    setPage(1)
  }
  
  // 处理价格筛选
  const handlePriceFilter = (filter: PriceFilter) => {
    setPriceFilter(filter)
    setPage(1)
  }
  
  // 处理评分筛选
  const handleRatingFilter = (rating: number) => {
    setMinRating(rating === 0 ? undefined : rating)
    setPage(1)
  }
  
  // 处理排序
  const handleSortChange = (sort: SortBy) => {
    setSortBy(sort)
    setPage(1)
  }
  
  // 处理安装
  const handleInstall = (skillId: number) => {
    installSkill.mutate(skillId)
  }
  
  // 渲染技能卡片
  const renderSkillCard = (skill: PublishedSkill) => {
    const isPaid = parseFloat(skill.price) > 0
    
    return (
      <Card
        hoverable
        className="skill-card"
        cover={
          <div className="skill-card-cover">
            <div className="skill-icon">
              {skill.name.charAt(0).toUpperCase()}
            </div>
            {skill.is_featured && (
              <Tag color="gold" className="featured-tag">精选</Tag>
            )}
          </div>
        }
        actions={[
          <Button
            type="primary"
            size="small"
            onClick={() => handleInstall(skill.id)}
            loading={installSkill.isPending}
          >
            {isPaid ? `¥${skill.price}` : '安装'}
          </Button>,
        ]}
      >
        <Card.Meta
          title={
            <div className="skill-title">
              <span>{skill.name}</span>
              {skill.category && (
                <Tag color="blue" className="category-tag">{skill.category}</Tag>
              )}
            </div>
          }
          description={
            <div className="skill-description">
              {skill.description || '暂无描述'}
            </div>
          }
        />
        <div className="skill-stats">
          <div className="stat-item">
            <StarFilled className="star-icon" />
            <span>{parseFloat(skill.rating).toFixed(1)}</span>
            <span className="stat-secondary">({skill.rating_count})</span>
          </div>
          <div className="stat-item">
            <DownloadOutlined />
            <span>{skill.download_count}</span>
          </div>
          <div className="stat-item">
            <Tag>v{skill.version}</Tag>
          </div>
        </div>
      </Card>
    )
  }
  
  // 渲染列表项
  const renderListItem = (skill: PublishedSkill) => {
    const isPaid = parseFloat(skill.price) > 0
    
    return (
      <List.Item
        actions={[
          <Button
            type="primary"
            onClick={() => handleInstall(skill.id)}
            loading={installSkill.isPending}
          >
            {isPaid ? `¥${skill.price}` : '安装'}
          </Button>,
        ]}
      >
        <List.Item.Meta
          avatar={
            <div className="skill-avatar">
              {skill.name.charAt(0).toUpperCase()}
            </div>
          }
          title={
            <div className="list-skill-title">
              <span>{skill.name}</span>
              {skill.is_featured && <Tag color="gold">精选</Tag>}
              {skill.category && <Tag color="blue">{skill.category}</Tag>}
              <Tag>v{skill.version}</Tag>
            </div>
          }
          description={
            <div>
              <div className="skill-description-text">
                {skill.description || '暂无描述'}
              </div>
              <div className="skill-stats-inline">
                <span><StarFilled className="star-icon" /> {parseFloat(skill.rating).toFixed(1)} ({skill.rating_count})</span>
                <span><DownloadOutlined /> {skill.download_count}</span>
              </div>
            </div>
          }
        />
      </List.Item>
    )
  }
  
  // 分类侧边栏
  const CategorySidebar = ({ mode = 'desktop' }: { mode?: 'desktop' | 'mobile' }) => (
    <div className={`category-sidebar ${mode}`}>
      <div className="sidebar-title">分类</div>
      <div className="category-list">
        {categories?.map((cat) => (
          <div
            key={cat.name}
            className={`category-item ${category === cat.name ? 'active' : ''}`}
            onClick={() => {
              handleCategoryChange(cat.name)
              if (mode === 'mobile') setDrawerVisible(false)
            }}
          >
            <span>{cat.name}</span>
            <span className="count">{cat.count}</span>
          </div>
        ))}
      </div>
    </div>
  )
  
  // 筛选面板
  const FilterPanel = () => (
    <div className="filter-panel">
      <Row gutter={[16, 16]} align="middle">
        <Col xs={24} sm={12} md={8}>
          <div className="filter-label">价格</div>
          <Radio.Group
            value={priceFilter}
            onChange={(e) => handlePriceFilter(e.target.value)}
            buttonStyle="solid"
            size="small"
          >
            <Radio.Button value="all">全部</Radio.Button>
            <Radio.Button value="free">免费</Radio.Button>
            <Radio.Button value="paid">付费</Radio.Button>
          </Radio.Group>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <div className="filter-label">评分</div>
          <Rate
            allowClear
            value={minRating || 0}
            onChange={handleRatingFilter}
            character={<StarFilled />}
          />
        </Col>
        
        <Col xs={24} sm={24} md={8}>
          <div className="filter-label">排序</div>
          <Select
            value={sortBy}
            onChange={handleSortChange}
            style={{ width: '100%' }}
          >
            <Option value="popular">
              <DownloadOutlined /> 最热
            </Option>
            <Option value="latest">
              <StarOutlined /> 最新
            </Option>
            <Option value="rating">
              <StarFilled /> 评分
            </Option>
          </Select>
        </Col>
      </Row>
    </div>
  )
  
  return (
    <div className="skill-search-page">
      {/* 移动端筛选抽屉 */}
      <Drawer
        title="分类"
        placement="left"
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        width={280}
      >
        <CategorySidebar mode="mobile" />
      </Drawer>
      
      {/* 搜索栏 */}
      <div className="search-header">
        <div className="search-bar-container">
          <AutoComplete
            style={{ width: '100%' }}
            options={suggestions.map(s => ({ value: s }))}
            onSearch={handleSearch}
            onSelect={handleSearch}
            value={searchKeyword}
            onChange={(value) => {
              setSearchKeyword(value)
              debouncedSearch(value)
            }}
          >
            <Search
              placeholder="搜索技能名称或描述..."
              allowClear
              enterButton={<><SearchOutlined /> 搜索</>}
              size="large"
              loading={isLoading && searchKeyword !== debouncedKeyword}
            />
          </AutoComplete>
        </div>
        
        <FilterPanel />
      </div>
      
      {/* 主内容区 */}
      <div className="search-content">
        {/* 桌面端侧边栏 */}
        <div className="desktop-sidebar">
          <Affix offsetTop={20}>
            <CategorySidebar mode="desktop" />
          </Affix>
        </div>
        
        {/* 结果区域 */}
        <div className="results-area">
          {/* 工具栏 */}
          <div className="results-toolbar">
            <div className="toolbar-left">
              <Button
                className="mobile-filter-btn"
                icon={<FilterOutlined />}
                onClick={() => setDrawerVisible(true)}
              >
                分类
              </Button>
              <span className="result-count">
                共 {data?.total || 0} 个技能
              </span>
            </div>
            
            <div className="toolbar-right">
              <Radio.Group
                value={viewMode}
                onChange={(e) => setViewMode(e.target.value)}
                buttonStyle="solid"
                size="small"
              >
                <Radio.Button value="grid">
                  <AppstoreOutlined />
                </Radio.Button>
                <Radio.Button value="list">
                  <BarsOutlined />
                </Radio.Button>
              </Radio.Group>
            </div>
          </div>
          
          {/* 加载状态 */}
          {isLoading && (
            <div className="loading-container">
              <Spin size="large" />
            </div>
          )}
          
          {/* 错误状态 */}
          {isError && (
            <Empty
              description="加载失败，请重试"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
          
          {/* 无结果 */}
          {!isLoading && !isError && data?.items.length === 0 && (
            <Empty
              description={
                <span>
                  未找到"{debouncedKeyword}"相关的技能
                  <br />
                  <small>试试其他关键词或清除筛选条件</small>
                </span>
              }
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
          
          {/* 结果列表 - 网格视图 */}
          {!isLoading && !isError && data && viewMode === 'grid' && (
            <>
              <Row gutter={[16, 16]}>
                {data.items.map((skill) => (
                  <Col xs={24} sm={12} md={8} lg={6} key={skill.id}>
                    {renderSkillCard(skill)}
                  </Col>
                ))}
              </Row>
              
              {/* 分页 */}
              {data.has_more && (
                <div className="load-more">
                  <Button
                    type="primary"
                    size="large"
                    onClick={() => setPage(page + 1)}
                    loading={isLoading}
                  >
                    加载更多
                  </Button>
                </div>
              )}
              
              <div className="pagination-container">
                <Pagination
                  current={page}
                  pageSize={pageSize}
                  total={data.total}
                  onChange={(p, ps) => {
                    setPage(p)
                    setPageSize(ps)
                  }}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(total) => `共 ${total} 个`}
                  pageSizeOptions={['12', '24', '48']}
                />
              </div>
            </>
          )}
          
          {/* 结果列表 - 列表视图 */}
          {!isLoading && !isError && data && viewMode === 'list' && (
            <>
              <List
                itemLayout="vertical"
                dataSource={data.items}
                renderItem={renderListItem}
              />
              
              <div className="pagination-container">
                <Pagination
                  current={page}
                  pageSize={pageSize}
                  total={data.total}
                  onChange={(p, ps) => {
                    setPage(p)
                    setPageSize(ps)
                  }}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(total) => `共 ${total} 个`}
                  pageSizeOptions={['12', '24', '48']}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
