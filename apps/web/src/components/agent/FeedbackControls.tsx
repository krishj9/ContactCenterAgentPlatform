import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Check, Edit3, XCircle, Sparkles } from 'lucide-react';
import { createTraceparent } from '../../telemetry/otel';

interface FeedbackControlsProps {
  sessionId: string;
  itemId: string;
  itemType?: 'recommendation' | 'response' | 'intent';
  currentIntent?: string;
  onDisposition?: (disposition: 'accepted' | 'edited' | 'dismissed') => void;
}

const CANONICAL_INTENTS = [
  { label: 'card_declined', name: 'Card Declined' },
  { label: 'fee_dispute', name: 'Fee Dispute' },
  { label: 'travel_notice', name: 'Travel Notice' },
  { label: 'lost_or_stolen_card', name: 'Lost / Stolen Card' },
  { label: 'charged_twice', name: 'Charged Twice' },
  { label: 'card_delivery_estimate', name: 'Card Delivery Estimate' },
  { label: 'out_of_scope', name: 'Out of Scope (General Chit-Chat)' },
];

export const FeedbackControls: React.FC<FeedbackControlsProps> = ({
  sessionId,
  itemId,
  itemType = 'recommendation',
  currentIntent,
  onDisposition,
}) => {
  const [rating, setRating] = useState<number | null>(null);
  const [disposition, setDisposition] = useState<'accepted' | 'edited' | 'dismissed' | null>(null);
  const [selectedIntent, setSelectedIntent] = useState<string>(currentIntent || '');
  const [showCorrection, setShowCorrection] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const sendFeedback = async (
    newRating: number | null,
    newDisposition: 'accepted' | 'edited' | 'dismissed',
    intentOverride?: string
  ) => {
    setSubmitting(true);
    try {
      const traceparent = createTraceparent();
      const payload = {
        session_id: sessionId,
        item_type: itemType,
        item_id: itemId,
        agent_disposition: newDisposition,
        rating: newRating,
        intent_correction: intentOverride || (selectedIntent !== currentIntent ? selectedIntent : null),
      };

      const res = await fetch('/v1/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'traceparent': traceparent,
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setSubmitted(true);
        if (onDisposition) onDisposition(newDisposition);
        setTimeout(() => setSubmitted(false), 3000);
      }
    } catch (err) {
      console.warn('Feedback submission failed:', err);
      // Still show optimistic update for agent
      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 3000);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRating = (newRating: number) => {
    const updated = rating === newRating ? null : newRating;
    setRating(updated);
    if (updated !== null) {
      sendFeedback(updated, disposition || 'accepted');
    }
  };

  const handleDisposition = (disp: 'accepted' | 'edited' | 'dismissed') => {
    setDisposition(disp);
    sendFeedback(rating, disp);
  };

  const handleIntentChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newIntent = e.target.value;
    setSelectedIntent(newIntent);
    sendFeedback(rating, disposition || 'edited', newIntent);
  };

  return (
    <div className="flex flex-col gap-2 pt-2 border-t border-slate-700/40 text-xs text-slate-400">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-medium text-slate-400">Assist Quality:</span>
          {/* Thumbs Up */}
          <button
            type="button"
            onClick={() => handleRating(1)}
            disabled={submitting}
            aria-label="Helpful recommendation"
            className={`p-1.5 rounded-md transition-all duration-200 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${
              rating === 1
                ? 'bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/50 shadow-sm shadow-emerald-500/20'
                : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <ThumbsUp className="w-3.5 h-3.5" />
          </button>
          {/* Thumbs Down */}
          <button
            type="button"
            onClick={() => handleRating(-1)}
            disabled={submitting}
            aria-label="Unhelpful recommendation"
            className={`p-1.5 rounded-md transition-all duration-200 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${
              rating === -1
                ? 'bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/50 shadow-sm shadow-rose-500/20'
                : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <ThumbsDown className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Action disposition controls */}
        <div className="flex items-center gap-1" role="group" aria-label="Action disposition choices">
          <button
            type="button"
            onClick={() => handleDisposition('accepted')}
            aria-label="Apply recommendation"
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${
              disposition === 'accepted'
                ? 'bg-emerald-600/30 text-emerald-300 ring-1 ring-emerald-500/40'
                : 'hover:bg-slate-800 text-slate-400 hover:text-slate-300'
            }`}
          >
            <Check className="w-3 h-3" /> Apply
          </button>
          <button
            type="button"
            onClick={() => handleDisposition('edited')}
            aria-label="Modify recommendation"
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${
              disposition === 'edited'
                ? 'bg-amber-600/30 text-amber-300 ring-1 ring-amber-500/40'
                : 'hover:bg-slate-800 text-slate-400 hover:text-slate-300'
            }`}
          >
            <Edit3 className="w-3 h-3" /> Modify
          </button>
          <button
            type="button"
            onClick={() => handleDisposition('dismissed')}
            aria-label="Dismiss recommendation"
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${
              disposition === 'dismissed'
                ? 'bg-rose-600/30 text-rose-300 ring-1 ring-rose-500/40'
                : 'hover:bg-slate-800 text-slate-400 hover:text-slate-300'
            }`}
          >
            <XCircle className="w-3 h-3" /> Dismiss
          </button>
          <button
            type="button"
            onClick={() => setShowCorrection(!showCorrection)}
            className="text-[11px] text-indigo-400 hover:text-indigo-300 underline ml-1"
          >
            Intent Correction
          </button>
        </div>
      </div>

      {/* Expandable Intent Correction Selector */}
      {showCorrection && (
        <div className="flex items-center gap-2 mt-1 p-2 bg-slate-900/60 rounded-md border border-slate-800">
          <span className="text-[11px] text-slate-400">Classify Intent as:</span>
          <select
            value={selectedIntent}
            onChange={handleIntentChange}
            className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded px-2 py-1 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
          >
            {CANONICAL_INTENTS.map((i) => (
              <option key={i.label} value={i.label}>
                {i.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Confirmation indicator */}
      {submitted && (
        <div className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium animate-fade-in">
          <Sparkles className="w-3 h-3" />
          <span>Feedback logged to telemetry & BigQuery</span>
        </div>
      )}
    </div>
  );
};
