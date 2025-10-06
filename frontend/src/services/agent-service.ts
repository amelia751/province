/**
 * Agent Service for communicating with backend AI agents
 * Handles session management, message routing, and real-time updates
 */

export interface AgentSession {
  sessionId: string;
  agentName: string;
  agentId: string;
  matterId?: string;
  status: 'active' | 'inactive';
}

export interface ChatRequest {
  message: string;
  sessionId?: string;
  agentName: string;
  matterId?: string;
  enableTrace?: boolean;
}

export interface ChatResponse {
  response: string;
  sessionId: string;
  agentName: string;
  matterId?: string;
  citations: Array<{
    title: string;
    url: string;
    snippet: string;
  }>;
  trace?: any;
}

export interface AgentInfo {
  name: string;
  agentId: string;
  description: string;
  foundationModel: string;
  knowledgeBases: string[];
  actionGroups: string[];
}

class AgentService {
  private baseUrl: string;
  private sessions: Map<string, AgentSession> = new Map();

  constructor() {
    // Use Next.js API routes which proxy to backend
    this.baseUrl = '/api';
  }

  /**
   * Create a new agent session
   */
  async createSession(agentName: string, matterId?: string): Promise<AgentSession> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_name: agentName,
          matter_id: matterId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(errorData.error || `Failed to create session: ${response.statusText}`);
      }

      const data = await response.json();
      
      const session: AgentSession = {
        sessionId: data.session_id,
        agentName: agentName,
        agentId: data.agent_id,
        matterId: data.matter_id,
        status: 'active',
      };

      this.sessions.set(session.sessionId, session);
      return session;
    } catch (error) {
      console.error('Error creating agent session:', error);
      throw error;
    }
  }

  /**
   * Send a message to an agent
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: request.message,
          session_id: request.sessionId,
          agent_name: request.agentName,
          matter_id: request.matterId,
          enable_trace: request.enableTrace || false,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(errorData.error || `Failed to send message: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Update session if new one was created
      if (data.session_id && data.session_id !== request.sessionId) {
        const session = this.sessions.get(request.sessionId || '');
        if (session) {
          session.sessionId = data.session_id;
          this.sessions.set(data.session_id, session);
          if (request.sessionId) {
            this.sessions.delete(request.sessionId);
          }
        }
      }

      return {
        response: data.response,
        sessionId: data.session_id,
        agentName: data.agent_name,
        matterId: data.matter_id,
        citations: data.citations || [],
        trace: data.trace,
      };
    } catch (error) {
      console.error('Error sending message to agent:', error);
      throw error;
    }
  }

  /**
   * Get session information
   */
  async getSession(sessionId: string): Promise<AgentSession | null> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/sessions/${sessionId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to get session: ${response.statusText}`);
      }

      const data = await response.json();
      
      const session: AgentSession = {
        sessionId: data.session_id,
        agentName: '', // Will need to be tracked separately
        agentId: data.agent_id,
        status: 'active',
      };

      return session;
    } catch (error) {
      console.error('Error getting session:', error);
      return null;
    }
  }

  /**
   * Close an agent session
   */
  async closeSession(sessionId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        this.sessions.delete(sessionId);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error closing session:', error);
      return false;
    }
  }

  /**
   * List available agents
   */
  async listAgents(): Promise<AgentInfo[]> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/agents`);
      
      if (!response.ok) {
        throw new Error(`Failed to list agents: ${response.statusText}`);
      }

      const data = await response.json();
      
      return data.agents.map((agent: any) => ({
        name: agent.name,
        agentId: agent.agent_id,
        description: agent.description,
        foundationModel: agent.foundation_model,
        knowledgeBases: agent.knowledge_bases,
        actionGroups: agent.action_groups,
      }));
    } catch (error) {
      console.error('Error listing agents:', error);
      throw error;
    }
  }

  /**
   * Get detailed agent information
   */
  async getAgentInfo(agentName: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/agents/${agentName}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get agent info: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting agent info:', error);
      throw error;
    }
  }

  /**
   * Get agent system statistics
   */
  async getStats(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/stats`);
      
      if (!response.ok) {
        throw new Error(`Failed to get stats: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting agent stats:', error);
      throw error;
    }
  }

  /**
   * Check agent system health
   */
  async healthCheck(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/health`);
      
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Agent health check failed:', error);
      throw error;
    }
  }

  /**
   * Get local session
   */
  getLocalSession(sessionId: string): AgentSession | undefined {
    return this.sessions.get(sessionId);
  }

  /**
   * List local sessions
   */
  getLocalSessions(): AgentSession[] {
    return Array.from(this.sessions.values());
  }
}

// Export singleton instance
export const agentService = new AgentService();