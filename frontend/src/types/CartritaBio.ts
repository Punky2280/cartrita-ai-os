export type AgentSpec = {
  id: string;
  name: string;
  role: string;
  model: string;
};

export type StorySection = {
  id: string;
  title: string;
  summary: string;
  content: string;
};

export type CartritaBio = {
  name: string;
  title: string;
  origin: string;
  heritage: string;
  location: string;
  mission: string;
  values: string[];
  personality: string[];
  capabilities: string[];
  agents: AgentSpec[];
  quotes: string[];
  story: StorySection[];
};
