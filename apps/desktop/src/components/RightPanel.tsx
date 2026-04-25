import { Bot, CheckCircle2, Lightbulb, Play } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import type { AgentAction, ChatMessage } from "../types/studio";

type RightPanelProps = {
  messages: ChatMessage[];
  actions: AgentAction[];
};

export function RightPanel({ messages, actions }: RightPanelProps) {
  return (
    <aside className="right-panel">
      <section className="right-section chat-section">
        <div className="section-title">
          <Bot size={16} />
          <span>AI Chat Panel</span>
        </div>
        <div className="chat-list">
          {messages.map((message) => (
            <div className={`chat-message chat-${message.role}`} key={message.id}>
              <strong>{message.role}</strong>
              <p>{message.body}</p>
            </div>
          ))}
        </div>
        <div className="chat-input-row">
          <input value="Review ERC and suggest fixes" readOnly />
          <button title="Send">
            <Play size={16} />
          </button>
        </div>
      </section>

      <section className="right-section">
        <div className="section-title">
          <CheckCircle2 size={16} />
          <span>Agent Actions</span>
        </div>
        <div className="action-list">
          {actions.map((action) => (
            <div className="action-row" key={action.id}>
              <span>{action.action}</span>
              <StatusBadge status={action.status} />
            </div>
          ))}
        </div>
      </section>

      <section className="right-section">
        <div className="section-title">
          <Lightbulb size={16} />
          <span>Suggested Fixes</span>
        </div>
        <div className="fix-list">
          <button>Add explicit power flags for generated power rails</button>
          <button>Replace placeholder USB audio bridge with selected part</button>
          <button>Attach decoupling template to FPGA power pins</button>
        </div>
      </section>
    </aside>
  );
}
