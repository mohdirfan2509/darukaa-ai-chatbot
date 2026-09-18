export interface EvidenceItem {
  source_title: string;
  organization?: string | null;
  authors?: string | null;
  publication_year?: number | null;
  url?: string | null;
  source_type?: string | null;
  relevant_snippet: string;
  similarity?: number | null;
}

export interface Recommendation {
  title: string;
  action: string;
  scientific_reasoning: string;
  impacted_metrics: string[];
  expected_direction: string;
  estimated_effect?: string | null;
  time_horizon: string;
  confidence: number;
  evidence: EvidenceItem[];
}

export interface StructuredAIResponse {
  answer: string;
  environmental_assessment: {
    summary: string;
    variables_considered: string[];
  };
  reasoning_summary: string[];
  recommendations: Recommendation[];
  missing_information: string[];
  assumptions: string[];
  retrieval: {
    sources_used: number;
    chunks_used: number;
  };
  environmental_context: Record<string, unknown>;
  needs_clarification: boolean;
  clarification_questions: string[];
}

export interface ConversationSummary {
  id: string;
  title?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: string;
  content: string;
  structured_payload?: StructuredAIResponse | null;
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  title?: string | null;
  created_at: string;
  updated_at: string;
  messages: Message[];
  context?: {
    known_variables: Record<string, unknown>;
    missing_variables: string[];
    environmental_state: Record<string, unknown>;
    assumptions: string[];
  } | null;
}

export interface RetrievedChunk {
  chunk_id: string;
  content: string;
  similarity: number;
  topic?: string | null;
  metadata: Record<string, unknown>;
  source: Record<string, unknown>;
}

export interface DemoScenario {
  id: string;
  title: string;
  description: string;
  label: string;
  prompt: string;
  followUps?: string[];
}
