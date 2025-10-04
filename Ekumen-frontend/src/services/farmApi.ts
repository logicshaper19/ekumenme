/**
 * Farm Data API Service
 * Connects frontend to backend farm data APIs
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

// Types matching our backend API responses
export interface ParcelleResponse {
  id: string
  nom: string
  surface_ha: number
  surface_mesuree_ha?: number
  culture_code?: string
  variete?: string
  date_semis?: string
  bbch_stage?: number
  commune_insee?: string
  millesime: number
  geometrie_vide: boolean
  succession_cultures?: any
  culture_intermediaire?: any
}

export interface InterventionResponse {
  id: string
  uuid_intervention: string
  type_intervention: string
  id_type_intervention?: number
  date_intervention: string
  date_debut: string
  date_fin: string
  surface_travaillee_ha: number
  id_culture?: number
  materiel_utilise?: string
  intrants?: any
  parcelle_id: string
  siret: string
}

export interface ExploitationResponse {
  siret: string
  nom: string
  region_code?: string
  department_code?: string
  commune_insee?: string
  surface_totale_ha: number
  type_exploitation?: string
  bio: boolean
  certification_bio?: string
  date_certification_bio?: string
  extra_data?: any
}

export interface ExploitationStatsResponse {
  exploitation: ExploitationResponse
  parcelle_count: number
  intervention_count: number
  total_surface_ha: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pages: number
  per_page: number
  has_next: boolean
  has_prev: boolean
}

export interface FarmOverviewResponse {
  total_farms: number
  total_parcelles: number
  total_surface_ha: number
  total_interventions: number
  recent_interventions: number
  bio_farms: number
  avg_parcelles_per_farm: number
}

export interface CultureDistributionResponse {
  culture_code: string
  culture_name?: string
  parcelle_count: number
  total_surface_ha: number
  percentage: number
}

export interface InterventionTimelineResponse {
  date: string
  intervention_count: number
  total_surface_ha: number
  intervention_types: Record<string, number>
}

export interface FarmDashboardResponse {
  overview: FarmOverviewResponse
  culture_distribution: CultureDistributionResponse[]
  recent_interventions: InterventionTimelineResponse[]
  farms: any[]
}

// Helper function to get auth token
const getAuthToken = (): string | null => {
  return localStorage.getItem('authToken')
}

// Helper function to make authenticated requests
const makeRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const token = getAuthToken()
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

// Parcelles API
export const parcellesApi = {
  // Get all parcelles with pagination and filters
  getParcelles: async (params: {
    skip?: number
    limit?: number
    farm_siret?: string
    culture_filter?: string
  } = {}): Promise<PaginatedResponse<ParcelleResponse>> => {
    const searchParams = new URLSearchParams()
    if (params.skip !== undefined) searchParams.append('skip', params.skip.toString())
    if (params.limit !== undefined) searchParams.append('limit', params.limit.toString())
    if (params.farm_siret) searchParams.append('farm_siret', params.farm_siret)
    if (params.culture_filter) searchParams.append('culture_filter', params.culture_filter)
    
    const queryString = searchParams.toString()
    return makeRequest<PaginatedResponse<ParcelleResponse>>(
      `/farm/parcelles/${queryString ? `?${queryString}` : ''}`
    )
  },

  // Get specific parcelle by ID
  getParcelle: async (id: string): Promise<ParcelleResponse> => {
    return makeRequest<ParcelleResponse>(`/farm/parcelles/${id}`)
  },

  // Get parcelles by farm SIRET
  getParcellesByFarm: async (farmSiret: string): Promise<ParcelleResponse[]> => {
    return makeRequest<ParcelleResponse[]>(`/farm/parcelles/farm/${farmSiret}`)
  },
}

// Interventions API
export const interventionsApi = {
  // Get all interventions with pagination and filters
  getInterventions: async (params: {
    skip?: number
    limit?: number
    farm_siret?: string
    parcelle_id?: string
    intervention_type?: string
  } = {}): Promise<PaginatedResponse<InterventionResponse>> => {
    const searchParams = new URLSearchParams()
    if (params.skip !== undefined) searchParams.append('skip', params.skip.toString())
    if (params.limit !== undefined) searchParams.append('limit', params.limit.toString())
    if (params.farm_siret) searchParams.append('farm_siret', params.farm_siret)
    if (params.parcelle_id) searchParams.append('parcelle_id', params.parcelle_id)
    if (params.intervention_type) searchParams.append('intervention_type', params.intervention_type)
    
    const queryString = searchParams.toString()
    return makeRequest<PaginatedResponse<InterventionResponse>>(
      `/farm/interventions/${queryString ? `?${queryString}` : ''}`
    )
  },

  // Get specific intervention by ID
  getIntervention: async (id: string): Promise<InterventionResponse> => {
    return makeRequest<InterventionResponse>(`/farm/interventions/${id}`)
  },

  // Get interventions by farm SIRET
  getInterventionsByFarm: async (farmSiret: string): Promise<InterventionResponse[]> => {
    return makeRequest<InterventionResponse[]>(`/farm/interventions/farm/${farmSiret}`)
  },

  // Get interventions by parcelle ID
  getInterventionsByParcelle: async (parcelleId: string): Promise<InterventionResponse[]> => {
    return makeRequest<InterventionResponse[]>(`/farm/interventions/parcelle/${parcelleId}`)
  },
}

// Exploitation API
export const exploitationApi = {
  // Get all exploitations
  getExploitations: async (): Promise<ExploitationResponse[]> => {
    return makeRequest<ExploitationResponse[]>('/farm/exploitation/')
  },

  // Get specific exploitation by SIRET
  getExploitation: async (siret: string): Promise<ExploitationResponse> => {
    return makeRequest<ExploitationResponse>(`/farm/exploitation/${siret}`)
  },

  // Get exploitation with statistics
  getExploitationStats: async (siret: string): Promise<ExploitationStatsResponse> => {
    return makeRequest<ExploitationStatsResponse>(`/farm/exploitation/${siret}/stats`)
  },
}

// Dashboard API
export const dashboardApi = {
  // Get farm overview
  getOverview: async (): Promise<FarmOverviewResponse> => {
    return makeRequest<FarmOverviewResponse>('/farm/dashboard/overview')
  },

  // Get culture distribution
  getCultureDistribution: async (): Promise<CultureDistributionResponse[]> => {
    return makeRequest<CultureDistributionResponse[]>('/farm/dashboard/culture-distribution')
  },

  // Get intervention timeline
  getInterventionTimeline: async (days: number = 30): Promise<InterventionTimelineResponse[]> => {
    return makeRequest<InterventionTimelineResponse[]>(`/farm/dashboard/intervention-timeline?days=${days}`)
  },

  // Get complete dashboard
  getCompleteDashboard: async (): Promise<FarmDashboardResponse> => {
    return makeRequest<FarmDashboardResponse>('/farm/dashboard/complete')
  },
}

// Combined farm API
export const farmApi = {
  parcelles: parcellesApi,
  interventions: interventionsApi,
  exploitation: exploitationApi,
  dashboard: dashboardApi,
}

export default farmApi
