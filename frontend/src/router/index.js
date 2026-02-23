import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'
import { TokenManager } from '../api/service'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', name: 'Dashboard', component: () => import('../components/Dashboard.vue') },
      { path: 'teams', name: 'Teams', component: () => import('../components/TeamsPage.vue'), meta: { permission: 'teams' } },
      { path: 'players', name: 'Players', component: () => import('../components/PlayersPage.vue'), meta: { permission: 'players' } },
      { path: 'matches', name: 'Matches', component: () => import('../components/MatchesPage.vue'), meta: { permission: 'matches' } },
      { path: 'seasons', name: 'Seasons', component: () => import('../components/SeasonsPage.vue'), meta: { permission: 'seasons' } },
      { path: 'competitions', name: 'Competitions', component: () => import('../components/CompetitionsPage.vue'), meta: { permission: 'competitions' } },
      { path: 'coaches', name: 'Coaches', component: () => import('../components/CoachesPage.vue'), meta: { permission: 'coaches' } },
      { path: 'contracts', name: 'Contracts', component: () => import('../components/ContractsPage.vue'), meta: { permission: 'contracts' } },
      { path: 'transfers', name: 'Transfers', component: () => import('../components/TransfersPage.vue'), meta: { permission: 'transfers' } },
      { path: 'training-plans', name: 'TrainingPlans', component: () => import('../components/TrainingPlansPage.vue'), meta: { permission: 'training' } },
      { path: 'finances', name: 'Finances', component: () => import('../components/FinancesPage.vue'), meta: { permission: 'finances' } },
      { path: 'news', name: 'News', component: () => import('../components/NewsPage.vue'), meta: { permission: 'news' } },
      { path: 'profile', name: 'Profile', component: () => import('../components/Profile.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../components/Settings.vue') }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Auth.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isLoggedIn = TokenManager.isLoggedIn()

  // 未登录且访问非登录页，跳转到登录页
  if (to.path !== '/login' && !isLoggedIn) {
    next('/login')
    return
  }

  // 已登录且访问登录页，跳转到首页
  if (to.path === '/login' && isLoggedIn) {
    next('/')
    return
  }

  // 权限检查
  if (to.meta.permission && !userStore.hasPermission(to.meta.permission)) {
    ElMessage.warning('您没有权限访问该页面')
    next('/dashboard')
    return
  }

  next()
})

export default router
