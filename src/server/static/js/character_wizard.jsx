import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';

export default function CharacterWizard({ username }) {
  const [phase, setPhase] = useState('selectUniverse');
  const [universes, setUniverses] = useState([]);
  const [selectedUni, setSelectedUni] = useState(null);
  const [rulesetId, setRulesetId] = useState(null);
  const [history, setHistory] = useState([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');

  // Fetch universes on mount
  useEffect(() => {
    fetch('/api/universe/list')
      .then(res => res.json())
      .then(data => setUniverses(data))
      .catch(console.error);
  }, []);

  // When universe selected, extract its ruleset_id and start wizard
  const startWizard = () => {
    const uni = universes.find(u => u.id === selectedUni);
    if (!uni) return;
    setRulesetId(uni.ruleset_id);
    // Begin wizard
    fetch('/api/character/wizard', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ruleset_id: uni.ruleset_id, history: [] })
    })
      .then(res => res.json())
      .then(resp => {
        setQuestion(resp.question);
        setPhase('wizard');
      })
      .catch(console.error);
  };

  // Handle wizard submission
  const submitAnswer = () => {
    const newHistory = [...history, { question, answer }];
    setHistory(newHistory);
    fetch('/api/character/wizard', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ruleset_id: rulesetId, history: newHistory })
    })
      .then(res => res.json())
      .then(resp => {
        if (resp.complete) {
          // Final character_data
          return fetch('/character/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              username,
              universe_id: selectedUni,
              name: resp.name,
              character_data: resp.character_data
            })
          });
        } else {
          setQuestion(resp.question);
          setAnswer('');
        }
      })
      .then(res => {
        if (res && res.ok) {
          // Redirect to lobby
          window.location.href = `/lobby?username=${encodeURIComponent(username)}`;
        }
      })
      .catch(console.error);
  };

  return (
    <div className="p-4 max-w-lg mx-auto">
      {phase === 'selectUniverse' && (
        <div>
          <h2 className="text-xl font-bold mb-4">Select Your Universe</h2>
          <select
            className="w-full border p-2 rounded mb-4"
            value={selectedUni || ''}
            onChange={e => setSelectedUni(e.target.value)}
          >
            <option value="">-- Choose a universe --</option>
            {universes.map(u => (
              <option key={u.id} value={u.id}>{u.name}</option>
            ))}
          </select>
          <button
            className="bg-blue-600 text-white p-2 rounded"
            disabled={!selectedUni}
            onClick={startWizard}
          >Start Character Creation</button>
        </div>
      )}

      {phase === 'wizard' && (
        <div>
          <h2 className="text-xl font-bold mb-4">{question}</h2>
          <input
            className="w-full border p-2 rounded mb-4"
            value={answer}
            onChange={e => setAnswer(e.target.value)}
          />
          <button
            className="bg-green-600 text-white p-2 rounded"
            disabled={!answer}
            onClick={submitAnswer}
          >Submit Answer</button>
        </div>
      )}
    </div>
  );
}

// Mounting code
const container = document.getElementById('wizard-root');
if (container) {
  const username = container.getAttribute('data-username');
  const root = ReactDOM.createRoot(container);
  root.render(<CharacterWizard username={username} />);
}
