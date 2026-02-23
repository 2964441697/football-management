import api from './service'
import { TokenManager } from './service'

const endpoints = {
    // Auth
    login: (data) => api.post('/auth/login', data).then(res => {
        // 保存 token
        if (res.access_token) {
            TokenManager.setTokens(res.access_token, res.refresh_token)
            if (res.user) {
                localStorage.setItem('user', JSON.stringify(res.user))
            }
        }
        return res
    }),
    
    register: (data) => api.post('/auth/register', data).then(res => {
        // 注册成功后自动登录
        if (res.access_token) {
            TokenManager.setTokens(res.access_token, res.refresh_token)
            if (res.user) {
                localStorage.setItem('user', JSON.stringify(res.user))
            }
        }
        return res
    }),
    
    logout: () => {
        TokenManager.clearTokens()
        window.location.href = '/login'
    },
    
    refreshToken: () => api.post('/auth/refresh', {
        refresh_token: TokenManager.getRefreshToken()
    }),
    
    getCurrentUser: () => api.get('/auth/me'),
    updateUser: (data) => api.put('/auth/update', data),
    changePassword: (data) => api.put('/auth/change-password', data),
    uploadAvatar: (formData) => api.post('/auth/upload-avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),

    // Teams
    getTeams: (params = {}) => api.get('/teams', { params }).then(res => res && res.items ? res.items : res),
    getTeamsPaginated: (params = {}) => api.get('/teams', { params }),
    getTeam: (id) => api.get(`/teams/${id}`),
    createTeam: (data) => api.post('/teams', data),
    updateTeam: (id, data) => api.put(`/teams/${id}`, data),
    deleteTeam: (id) => api.delete(`/teams/${id}`),
    resetTeamIds: () => api.post('/teams/reset-ids'),

    // Seasons
    getSeasons: (params = {}) => api.get('/seasons', { params }).then(res => res && res.items ? res.items : res),
    getSeasonsPaginated: (params = {}) => api.get('/seasons', { params }),
    getSeason: (id) => api.get(`/seasons/${id}`),
    createSeason: (data) => api.post('/seasons', data),
    updateSeason: (id, data) => api.put(`/seasons/${id}`, data),
    deleteSeason: (id) => api.delete(`/seasons/${id}`),
    resetSeasonIds: () => api.post('/seasons/reset-ids'),

    // Matches
    getMatches: (params = {}) => api.get('/matches', { params }).then(res => res && res.items ? res.items : res),
    getMatchesPaginated: (params = {}) => api.get('/matches', { params }),
    getMatch: (id) => api.get(`/matches/${id}`),
    createMatch: (data) => api.post('/matches', data),
    updateMatch: (id, data) => api.put(`/matches/${id}`, data),
    deleteMatch: (id) => api.delete(`/matches/${id}`),
    resetMatchIds: () => api.post('/matches/reset-ids'),

    // Players - 支持后端分页
    getPlayers: (params = {}) => api.get('/players', { params }).then(res => res && res.items ? res.items : res),
    getPlayersPaginated: (params = {}) => api.get('/players', { params }),
    getPlayer: (id) => api.get(`/players/${id}`),
    createPlayer: (data) => api.post('/players', data),
    updatePlayer: (id, data) => api.put(`/players/${id}`, data),
    deletePlayer: (id) => api.delete(`/players/${id}`),
    batchDeletePlayers: (ids) => api.post('/players/batch-delete', { ids }),
    resetPlayerIds: () => api.post('/players/reset-ids'),
    uploadPlayerAvatar: (formData) => api.post('/players/upload-avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),

    // Coaches
    getCoaches: (params = {}) => api.get('/coaches', { params }).then(res => res && res.items ? res.items : res),
    getCoachesPaginated: (params = {}) => api.get('/coaches', { params }),
    getCoach: (id) => api.get(`/coaches/${id}`),
    createCoach: (data) => api.post('/coaches', data),
    updateCoach: (id, data) => api.put(`/coaches/${id}`, data),
    deleteCoach: (id) => api.delete(`/coaches/${id}`),
    resetCoachIds: () => api.post('/coaches/reset-ids'),
    uploadCoachAvatar: (formData) => api.post('/coaches/upload-avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),

    // Competitions
    getCompetitions: (params = {}) => api.get('/competitions', { params }).then(res => res && res.items ? res.items : res),
    getCompetitionsPaginated: (params = {}) => api.get('/competitions', { params }),
    getCompetition: (id) => api.get(`/competitions/${id}`),
    createCompetition: (data) => api.post('/competitions', data),
    updateCompetition: (id, data) => api.put(`/competitions/${id}`, data),
    deleteCompetition: (id) => api.delete(`/competitions/${id}`),
    resetCompetitionIds: () => api.post('/competitions/reset-ids'),

    // News
    getNews: (params = {}) => api.get('/news', { params }).then(res => res && res.items ? res.items : res),
    getNewsPaginated: (params = {}) => api.get('/news', { params }),
    getNewsItem: (id) => api.get(`/news/${id}`),
    createNews: (data) => api.post('/news', data),
    updateNews: (id, data) => api.put(`/news/${id}`, data),
    deleteNews: (id) => api.delete(`/news/${id}`),
    resetNewsIds: () => api.post('/news/reset-ids'),

    // Finances
    getFinances: (params = {}) => api.get('/finances', { params }).then(res => res && res.items ? res.items : res),
    getFinancesPaginated: (params = {}) => api.get('/finances', { params }),
    getFinance: (id) => api.get(`/finances/${id}`),
    createFinance: (data) => api.post('/finances', data),
    updateFinance: (id, data) => api.put(`/finances/${id}`, data),
    deleteFinance: (id) => api.delete(`/finances/${id}`),
    resetFinanceIds: () => api.post('/finances/reset-ids'),

    // Training Plans
    getTrainingPlans: (params = {}) => api.get('/training-plans', { params }).then(res => res && res.items ? res.items : res),
    getTrainingPlansPaginated: (params = {}) => api.get('/training-plans', { params }),
    getTrainingPlan: (id) => api.get(`/training-plans/${id}`),
    createTrainingPlan: (data) => api.post('/training-plans', data),
    updateTrainingPlan: (id, data) => api.put(`/training-plans/${id}`, data),
    deleteTrainingPlan: (id) => api.delete(`/training-plans/${id}`),
    resetTrainingPlanIds: () => api.post('/training-plans/reset-ids'),

    // Contracts
    getContracts: (params = {}) => api.get('/contracts', { params }).then(res => res && res.items ? res.items : res),
    getContractsPaginated: (params = {}) => api.get('/contracts', { params }),
    getContract: (id) => api.get(`/contracts/${id}`),
    createContract: (data) => api.post('/contracts', data),
    updateContract: (id, data) => api.put(`/contracts/${id}`, data),
    deleteContract: (id) => api.delete(`/contracts/${id}`),
    resetContractIds: () => api.post('/contracts/reset-ids'),

    // Transfers
    getTransfers: (params = {}) => api.get('/transfers', { params }).then(res => res && res.items ? res.items : res),
    getTransfersPaginated: (params = {}) => api.get('/transfers', { params }),
    getTransfer: (id) => api.get(`/transfers/${id}`),
    createTransfer: (data) => api.post('/transfers', data),
    updateTransfer: (id, data) => api.put(`/transfers/${id}`, data),
    deleteTransfer: (id) => api.delete(`/transfers/${id}`),
    resetTransferIds: () => api.post('/transfers/reset-ids'),

    // Match Lineups
    getMatchLineups: (matchId) => api.get('/match-lineups', { params: { match_id: matchId } }),
    createMatchLineup: (data) => api.post('/match-lineups', data),
    updateMatchLineup: (id, data) => api.put(`/match-lineups/${id}`, data),
    deleteMatchLineup: (id) => api.delete(`/match-lineups/${id}`),

    // Match Events
    getMatchEvents: (matchId) => api.get('/match-events', { params: { match_id: matchId } }),
    createMatchEvent: (data) => api.post('/match-events', data),
    updateMatchEvent: (id, data) => api.put(`/match-events/${id}`, data),
    deleteMatchEvent: (id) => api.delete(`/match-events/${id}`),

    // Player Stats
    getPlayerStats: (playerId) => api.get('/player-stats', { params: { player_id: playerId } }),
    createPlayerStat: (data) => api.post('/player-stats', data),
    updatePlayerStat: (id, data) => api.put(`/player-stats/${id}`, data),

    // Finance Summary
    getFinanceSummary: (teamId) => api.get(`/finances/summary/team/${teamId}`),

    // Upcoming Training Plans
    getUpcomingTrainingPlans: () => api.get('/training-plans/upcoming'),

    // Expiring Contracts
    getExpiringContracts: () => api.get('/contracts/expiring'),

    // Stats & Dashboard
    getDashboardStats: () => api.get('/stats/dashboard'),

    // Export
    exportData: (resource) => {
        const baseURL = import.meta.env.VITE_API_BASE_URL || ''
        window.open(`${baseURL}/api/stats/export/${resource}`, '_blank')
    },

    // Batch Delete
    batchDelete: (resource, ids) => api.post('/stats/batch-delete', { resource, ids }),

    // Global Search
    globalSearch: (query) => api.get('/stats/search', { params: { q: query } }).then(res => ({ data: res })),

    // Image Upload
    uploadImage: (formData) => api.post('/auth/upload-avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    
    // Users (Admin)
    getUsers: () => api.get('/auth/users'),
    updateUserRole: (userId, role) => api.put('/auth/role', { user_id: userId, role }),
    getRoleChoices: () => api.get('/auth/roles/choices'),
    
    // Backgrounds
    getBackgrounds: () => api.get('/auth/backgrounds'),
    uploadBackground: (formData) => api.post('/auth/backgrounds/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    deleteBackground: (bgId) => api.delete(`/auth/backgrounds/${bgId}`)
}

export default endpoints
