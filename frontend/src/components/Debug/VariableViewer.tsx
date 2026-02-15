import React, { useState, useMemo } from 'react'
import { Tree, Tag, Empty, Input, Dropdown, Button, message } from 'antd'
import {
  SearchOutlined,
  CopyOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import type { TreeDataNode } from 'antd'
import type { DebugVariable } from '@/types/debug'
import styles from './VariableViewer.module.css'

interface VariableViewerProps {
  variables: DebugVariable[]
  onRefresh?: () => void
  onVariableClick?: (variable: DebugVariable) => void
}

// 获取值的显示颜色
const getTypeColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    string: '#ce9178',
    number: '#b5cea8',
    boolean: '#569cd6',
    null: '#569cd6',
    undefined: '#569cd6',
    object: '#9cdcfe',
    array: '#4ec9b0',
    function: '#dcdcaa'
  }
  return colorMap[type.toLowerCase()] || '#d4d4d4'
}

// 格式化值显示
const formatValue = (value: any, type: string): string => {
  switch (type.toLowerCase()) {
    case 'string':
      return `"${value}"`
    case 'boolean':
    case 'number':
      return String(value)
    case 'null':
      return 'null'
    case 'undefined':
      return 'undefined'
    case 'array':
      return `Array(${value?.length || 0})`
    case 'object':
      return value ? '{...}' : '{}'
    case 'function':
      return 'ƒ()'
    default:
      return String(value)
  }
}

// 将变量转换为树节点
const convertToTreeNodes = (variables: DebugVariable[], searchTerm: string = ''): TreeDataNode[] => {
  return variables
    .filter(v => !searchTerm || v.name.toLowerCase().includes(searchTerm.toLowerCase()))
    .map(variable => {
      const typeColor = getTypeColor(variable.type)
      const displayValue = formatValue(variable.value, variable.type)

      const node: TreeDataNode = {
        key: variable.name,
        title: (
          <div className={styles.variableItem}>
            <span className={styles.varName}>{variable.name}</span>
            <span className={styles.varSeparator}>:</span>
            <span className={styles.varType} style={{ color: typeColor }}>
              {variable.type}
            </span>
            <span className={styles.varValue} style={{ color: typeColor }}>
              {displayValue}
            </span>
          </div>
        ),
        icon: <span className={styles.varIcon} style={{ color: typeColor }}>●</span>
      }

      // 如果有子节点且可展开
      if (variable.expandable && variable.children && variable.children.length > 0) {
        node.children = convertToTreeNodes(variable.children)
      } else if (variable.expandable) {
        // 对于数组和对象，显示占位符
        if (variable.type === 'array' && Array.isArray(variable.value)) {
          node.children = variable.value.map((item: any, index: number) => ({
            key: `${variable.name}[${index}]`,
            title: (
              <div className={styles.variableItem}>
                <span className={styles.varName}>{index}</span>
                <span className={styles.varSeparator}>:</span>
                <span className={styles.varValue} style={{ color: getTypeColor(typeof item) }}>
                  {formatValue(item, typeof item)}
                </span>
              </div>
            )
          }))
        } else if (variable.type === 'object' && variable.value && typeof variable.value === 'object') {
          node.children = Object.entries(variable.value).map(([key, val]) => ({
            key: `${variable.name}.${key}`,
            title: (
              <div className={styles.variableItem}>
                <span className={styles.varName}>{key}</span>
                <span className={styles.varSeparator}>:</span>
                <span className={styles.varValue} style={{ color: getTypeColor(typeof val) }}>
                  {formatValue(val, typeof val)}
                </span>
              </div>
            )
          }))
        }
      }

      return node
    })
}

export default function VariableViewer({
  variables,
  onRefresh,
  onVariableClick
}: VariableViewerProps) {
  const [searchText, setSearchText] = useState('')
  const [expandedKeys, setExpandedKeys] = useState<string[]>([])
  const [selectedScope, setSelectedScope] = useState<'all' | 'local' | 'global' | 'closure'>('all')

  // 按作用域过滤
  const filteredVariables = useMemo(() => {
    let result = variables
    if (selectedScope !== 'all') {
      result = result.filter(v => v.scope === selectedScope)
    }
    return result
  }, [variables, selectedScope])

  // 树数据
  const treeData = useMemo(() => {
    return convertToTreeNodes(filteredVariables, searchText)
  }, [filteredVariables, searchText])

  // 复制值到剪贴板
  const copyValue = (variable: DebugVariable) => {
    const text = typeof variable.value === 'object'
      ? JSON.stringify(variable.value, null, 2)
      : String(variable.value)

    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板')
    }).catch(() => {
      message.error('复制失败')
    })
  }

  // 右键菜单
  const getContextMenu = (variable: DebugVariable) => ({
    items: [
      {
        key: 'copy',
        icon: <CopyOutlined />,
        label: '复制值',
        onClick: () => copyValue(variable)
      }
    ]
  })

  return (
    <div className={styles.variableViewer}>
      <div className={styles.varToolbar}>
        <Input
          placeholder="搜索变量..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={e => setSearchText(e.target.value)}
          allowClear
          size="small"
          className={styles.searchInput}
        />
        <div className={styles.scopeTabs}>
          {(['all', 'local', 'global', 'closure'] as const).map(scope => (
            <Tag
              key={scope}
              color={selectedScope === scope ? 'blue' : 'default'}
              className={styles.scopeTab}
              onClick={() => setSelectedScope(scope)}
            >
              {scope === 'all' ? '全部' : scope}
            </Tag>
          ))}
        </div>
        <Button
          size="small"
          icon={<ReloadOutlined />}
          onClick={onRefresh}
          title="刷新变量"
        />
      </div>

      <div className={styles.varContainer}>
        {treeData.length > 0 ? (
          <Tree
            showIcon
            expandedKeys={expandedKeys}
            onExpand={setExpandedKeys}
            treeData={treeData}
            className={styles.varTree}
            onSelect={(keys, info) => {
              if (keys.length > 0) {
                const varName = keys[0] as string
                const variable = variables.find(v => v.name === varName)
                if (variable) {
                  onVariableClick?.(variable)
                }
              }
            }}
          />
        ) : (
          <Empty
            description="暂无变量"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            className={styles.emptyVars}
          />
        )}
      </div>
    </div>
  )
}
