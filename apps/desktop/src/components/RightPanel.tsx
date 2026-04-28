import { Bot, CheckCircle2, Lightbulb, Play } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import type { AgentAction, ChatMessage, JsonObject } from "../types/studio";

type RightPanelProps = {
  messages: ChatMessage[];
  actions: AgentAction[];
  suggestedFixes: JsonObject[];
};

export function RightPanel({ messages, actions, suggestedFixes }: RightPanelProps) {
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
          <span>Pipeline Actions</span>
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
          <span>Suggested Fixes ({suggestedFixes.length})</span>
        </div>
        <div className="fix-list">
          {suggestedFixes.length === 0 && <p className="bottom-copy">No fix suggestions available.</p>}
          {suggestedFixes.map((fix) => (
            <FixCard key={fix.id as string} fix={fix} />
          ))}
        </div>
      </section>
    </aside>
  );
}

function FixCard({ fix }: { fix: JsonObject }) {
  const severity = (fix.severity as string) ?? "info";
  const title = (fix.title as string) ?? "Unknown fix";
  const target = fix.target as JsonObject | undefined;
  const symbol = target?.symbol as string | undefined;
  const pin = target?.pin as string | undefined;
  return (
    <button className="fix-card">
      <div className="fix-card-header">
        <span className={`fix-severity fix-severity-${severity}`}>{severity}</span>
        <span className="fix-card-title">{title}</span>
      </div>
      <div className="fix-card-target">
        {symbol && <span>{symbol}</span>}
        {pin && <span>.{pin}</span>}
      </div>
    </button>
  );
}
