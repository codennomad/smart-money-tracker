export type TransactionType = 'buy' | 'sell' | 'option_buy' | 'option_sell'
export type FilingSource = 'form4' | '13f' | '13d' | '13g' | 'congress' | 'darkpool' | 'options'
export type SentimentSignal = 'bullish' | 'bearish' | 'neutral'

export interface InsiderTrade {
  id: string
  ticker: string
  company: string
  insiderName: string
  insiderTitle: string
  transactionType: TransactionType
  shares: number
  pricePerShare: number
  totalValue: number
  filedAt: string
  transactionDate: string
  source: FilingSource
  formUrl: string
  anomalyScore?: number
}

export interface CongressTrade {
  id: string
  member: string
  party: 'D' | 'R' | 'I'
  chamber: 'house' | 'senate'
  ticker: string
  company: string
  transactionType: TransactionType
  amountMin: number
  amountMax: number
  transactionDate: string
  disclosedAt: string
  daysToDisclose: number
}

export interface OptionsFlow {
  id: string
  ticker: string
  expiry: string
  strike: number
  callPut: 'call' | 'put'
  premium: number
  volume: number
  openInterest: number
  volOiRatio: number
  unusualScore: number
  detectedAt: string
}

export interface DarkPoolPrint {
  id: string
  ticker: string
  shares: number
  price: number
  totalValue: number
  shortVolume: number
  shortExemptVolume: number
  totalVolume: number
  shortPct: number
  reportDate: string
}

export interface AnomalyAlert {
  id: string
  ticker: string
  alertType: 'cluster_buying' | 'congress_options_combo' | 'pre_earnings_flow' | 'unusual_volume'
  confidence: number
  description: string
  relatedIds: string[]
  detectedAt: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  hasNext: boolean
}
