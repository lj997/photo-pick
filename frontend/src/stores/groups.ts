import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Group, Photo } from '../types/photo'
import { listGroups, detectSimilarGroups, updateGroupPick, resetGroupPK } from '../api/groups'
import { updateMarks } from '../api/photos'

export const useGroupsStore = defineStore('groups', () => {
  const groups = ref<Group[]>([])
  const loading = ref(false)
  const detecting = ref(false)
  const currentGroupIndex = ref(0)
  const championIds = ref<string[]>([])
  const challengerIndex = ref(0)
  const threshold = ref(8)
  const pkCompareCount = ref(2)

  const currentGroup = computed(() => groups.value[currentGroupIndex.value] || null)

  const champions = computed<Photo[]>(() => {
    if (!currentGroup.value?.members) return []
    return currentGroup.value.members.filter(p => championIds.value.includes(p.id))
  })

  // 挑战者：排除冠军，但包含淘汰的（用于显示）
  const allChallengers = computed<Photo[]>(() => {
    if (!currentGroup.value?.members) return []
    return currentGroup.value.members.filter(p => !championIds.value.includes(p.id))
  })

  // 活跃挑战者：非冠军且未淘汰
  const challengers = computed<Photo[]>(() => {
    return allChallengers.value.filter(p => p.status !== 'rejected')
  })

  const currentChallenger = computed<Photo | null>(() => {
    return allChallengers.value[challengerIndex.value] || null
  })

  const primaryChampion = computed<Photo | null>(() => {
    return champions.value[0] || null
  })

  async function loadGroups(sessionId: string, groupType?: string) {
    loading.value = true
    try {
      groups.value = await listGroups(sessionId, groupType, true)
    } finally {
      loading.value = false
    }
  }

  async function triggerDetection(sessionId: string) {
    detecting.value = true
    try {
      await detectSimilarGroups(sessionId, threshold.value)
    } catch {
      detecting.value = false
    }
  }

  function onDetectionComplete(sessionId: string) {
    detecting.value = false
    loadGroups(sessionId, 'similar')
  }

  function enterGroup(index: number) {
    currentGroupIndex.value = index
    challengerIndex.value = 0
    const group = groups.value[index]
    if (group?.members?.length) {
      // 仅恢复之前已确认的冠军，不默认设置
      const pickId = group.pick_photo_id
      if (pickId && group.members.some(m => m.id === pickId)) {
        championIds.value = [pickId]
      } else {
        const accepted = group.members.filter(m => m.status === 'accepted')
        if (accepted.length > 0) {
          championIds.value = accepted.map(m => m.id)
        } else {
          championIds.value = []
        }
      }
    } else {
      championIds.value = []
    }
  }

  function setChampion(id: string) {
    championIds.value = [id]
    challengerIndex.value = 0
  }

  async function addChampion(id: string) {
    if (!championIds.value.includes(id)) {
      championIds.value.push(id)
    }
    // 标记为 accepted 持久化
    await updateMarks(id, { status: 'accepted' })
    if (currentGroup.value?.members) {
      const member = currentGroup.value.members.find(m => m.id === id)
      if (member) member.status = 'accepted'
    }
    // 调整挑战者索引
    if (challengerIndex.value >= allChallengers.value.length) {
      challengerIndex.value = Math.max(0, allChallengers.value.length - 1)
    }
    // 保存 pick_photo_id
    if (currentGroup.value) {
      await updateGroupPick(currentGroup.value.id, championIds.value[0])
    }
  }

  async function removeChampion(id: string) {
    championIds.value = championIds.value.filter(cid => cid !== id)
    // 恢复为 pending
    await updateMarks(id, { status: 'pending' })
    if (currentGroup.value?.members) {
      const member = currentGroup.value.members.find(m => m.id === id)
      if (member) member.status = 'pending'
    }
    // 更新 pick_photo_id
    if (currentGroup.value) {
      await updateGroupPick(currentGroup.value.id, championIds.value[0] || null)
    }
  }

  async function rejectChallenger(id: string) {
    await updateMarks(id, { status: 'rejected' })
    if (currentGroup.value?.members) {
      const member = currentGroup.value.members.find(m => m.id === id)
      if (member) member.status = 'rejected'
    }
  }

  async function unrejectPhoto(id: string) {
    await updateMarks(id, { status: 'pending' })
    if (currentGroup.value?.members) {
      const member = currentGroup.value.members.find(m => m.id === id)
      if (member) member.status = 'pending'
    }
  }

  async function resetGroup() {
    if (!currentGroup.value) return
    await resetGroupPK(currentGroup.value.id)
    if (currentGroup.value.members) {
      for (const m of currentGroup.value.members) {
        m.status = 'pending'
      }
    }
    currentGroup.value.pick_photo_id = null
    championIds.value = []
    challengerIndex.value = 0
  }

  function nextChallenger() {
    if (challengerIndex.value < allChallengers.value.length - 1) {
      challengerIndex.value++
    }
  }

  function prevChallenger() {
    if (challengerIndex.value > 0) {
      challengerIndex.value--
    }
  }

  function nextGroup() {
    if (currentGroupIndex.value < groups.value.length - 1) {
      enterGroup(currentGroupIndex.value + 1)
    }
  }

  function prevGroup() {
    if (currentGroupIndex.value > 0) {
      enterGroup(currentGroupIndex.value - 1)
    }
  }

  function updateMemberPhoto(photoId: string, data: Partial<Photo>) {
    for (const group of groups.value) {
      if (!group.members) continue
      const member = group.members.find(m => m.id === photoId)
      if (member) {
        Object.assign(member, data)
        break
      }
    }
  }

  return {
    groups,
    loading,
    detecting,
    currentGroupIndex,
    championIds,
    challengerIndex,
    threshold,
    pkCompareCount,
    currentGroup,
    champions,
    allChallengers,
    challengers,
    currentChallenger,
    primaryChampion,
    loadGroups,
    triggerDetection,
    onDetectionComplete,
    enterGroup,
    setChampion,
    addChampion,
    removeChampion,
    rejectChallenger,
    unrejectPhoto,
    resetGroup,
    nextChallenger,
    prevChallenger,
    nextGroup,
    prevGroup,
    updateMemberPhoto,
  }
})
