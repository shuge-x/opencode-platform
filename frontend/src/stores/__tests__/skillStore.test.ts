import { useSkillStore } from '../skillStore'

describe('useSkillStore', () => {
  beforeEach(() => {
    // Reset to initial state
    useSkillStore.setState({
      searchQuery: '',
      selectedCategory: 'all',
      loading: false,
    })
  })

  describe('initial state', () => {
    it('should have skills preloaded', () => {
      const { skills } = useSkillStore.getState()
      expect(skills.length).toBeGreaterThan(0)
    })

    it('should have installed skills filtered', () => {
      const { installedSkills, skills } = useSkillStore.getState()
      expect(installedSkills.length).toBeLessThanOrEqual(skills.length)
      expect(installedSkills.every(s => s.installed)).toBe(true)
    })

    it('should have empty search query initially', () => {
      const { searchQuery } = useSkillStore.getState()
      expect(searchQuery).toBe('')
    })

    it('should have "all" as default category', () => {
      const { selectedCategory } = useSkillStore.getState()
      expect(selectedCategory).toBe('all')
    })

    it('should not be loading initially', () => {
      const { loading } = useSkillStore.getState()
      expect(loading).toBe(false)
    })
  })

  describe('setSkills', () => {
    it('should update skills list', () => {
      const { setSkills } = useSkillStore.getState()
      const newSkills = [
        {
          id: '99',
          name: 'Test Skill',
          description: 'Test description',
          category: 'Test',
          version: '1.0.0',
          author: 'Test Author',
          downloads: 100,
          rating: 4.5,
          tags: ['test'],
          installed: false,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
        },
      ]

      setSkills(newSkills)

      const { skills } = useSkillStore.getState()
      expect(skills).toEqual(newSkills)
    })

    it('should update installedSkills when setting skills', () => {
      const { setSkills } = useSkillStore.getState()
      const newSkills = [
        {
          id: '1',
          name: 'Installed Skill',
          description: 'Test',
          category: 'Test',
          version: '1.0.0',
          author: 'Test',
          downloads: 100,
          rating: 4.5,
          tags: [],
          installed: true,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
        },
        {
          id: '2',
          name: 'Not Installed',
          description: 'Test',
          category: 'Test',
          version: '1.0.0',
          author: 'Test',
          downloads: 100,
          rating: 4.5,
          tags: [],
          installed: false,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
        },
      ]

      setSkills(newSkills)

      const { installedSkills } = useSkillStore.getState()
      expect(installedSkills.length).toBe(1)
      expect(installedSkills[0].id).toBe('1')
    })
  })

  describe('installSkill', () => {
    it('should mark skill as installed', () => {
      const { installSkill, skills } = useSkillStore.getState()
      const notInstalledSkill = skills.find(s => !s.installed)
      
      if (notInstalledSkill) {
        installSkill(notInstalledSkill.id)
        
        const updatedSkill = useSkillStore.getState().skills.find(s => s.id === notInstalledSkill.id)
        expect(updatedSkill?.installed).toBe(true)
      }
    })

    it('should increment download count when installing', () => {
      const { installSkill, skills } = useSkillStore.getState()
      const notInstalledSkill = skills.find(s => !s.installed)
      
      if (notInstalledSkill) {
        const originalDownloads = notInstalledSkill.downloads
        installSkill(notInstalledSkill.id)
        
        const updatedSkill = useSkillStore.getState().skills.find(s => s.id === notInstalledSkill.id)
        expect(updatedSkill?.downloads).toBe(originalDownloads + 1)
      }
    })

    it('should add skill to installedSkills list', () => {
      const { installSkill, skills } = useSkillStore.getState()
      const notInstalledSkill = skills.find(s => !s.installed)
      
      if (notInstalledSkill) {
        const originalCount = useSkillStore.getState().installedSkills.length
        installSkill(notInstalledSkill.id)
        
        const newCount = useSkillStore.getState().installedSkills.length
        expect(newCount).toBe(originalCount + 1)
      }
    })
  })

  describe('uninstallSkill', () => {
    it('should mark skill as not installed', () => {
      const { uninstallSkill, skills } = useSkillStore.getState()
      const installedSkill = skills.find(s => s.installed)
      
      if (installedSkill) {
        uninstallSkill(installedSkill.id)
        
        const updatedSkill = useSkillStore.getState().skills.find(s => s.id === installedSkill.id)
        expect(updatedSkill?.installed).toBe(false)
      }
    })

    it('should remove skill from installedSkills list', () => {
      const { uninstallSkill, skills } = useSkillStore.getState()
      const installedSkill = skills.find(s => s.installed)
      
      if (installedSkill) {
        const originalCount = useSkillStore.getState().installedSkills.length
        uninstallSkill(installedSkill.id)
        
        const newCount = useSkillStore.getState().installedSkills.length
        expect(newCount).toBe(originalCount - 1)
      }
    })
  })

  describe('setSearchQuery', () => {
    it('should update search query', () => {
      const { setSearchQuery } = useSkillStore.getState()
      setSearchQuery('code generator')
      
      const { searchQuery } = useSkillStore.getState()
      expect(searchQuery).toBe('code generator')
    })
  })

  describe('setSelectedCategory', () => {
    it('should update selected category', () => {
      const { setSelectedCategory } = useSkillStore.getState()
      setSelectedCategory('开发工具')
      
      const { selectedCategory } = useSkillStore.getState()
      expect(selectedCategory).toBe('开发工具')
    })
  })

  describe('setLoading', () => {
    it('should update loading state', () => {
      const { setLoading } = useSkillStore.getState()
      setLoading(true)
      
      const { loading } = useSkillStore.getState()
      expect(loading).toBe(true)
    })
  })

  describe('getSkillById', () => {
    it('should return skill when found', () => {
      const { getSkillById, skills } = useSkillStore.getState()
      const firstSkill = skills[0]
      
      const result = getSkillById(firstSkill.id)
      expect(result).toEqual(firstSkill)
    })

    it('should return undefined when skill not found', () => {
      const { getSkillById } = useSkillStore.getState()
      
      const result = getSkillById('non-existent-id')
      expect(result).toBeUndefined()
    })
  })
})
