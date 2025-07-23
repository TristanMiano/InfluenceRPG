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
  const [finalData, setFinalData] = useState(null); // {name, character_data}
  const [editData, setEditData] = useState({});

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
          setFinalData({ name: resp.name, character_data: resp.character_data });
          setEditData({ name: resp.name, ...resp.character_data });
          setPhase('finalize');
        } else {
          setQuestion(resp.question);
          setAnswer('');
        }
      })
      .catch(console.error);
  };

  const discardChanges = () => {
    if (finalData) {
      setEditData({ name: finalData.name, ...finalData.character_data });
    }
  };

  const saveCharacter = () => {
    const { name, ...charData } = editData;
    fetch('/character/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        universe_id: selectedUni,
        name,
        character_data: charData
      })
    })
      .then(res => { if (res.ok) window.location.href = `/lobby?username=${encodeURIComponent(username)}`; })
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

      {phase === 'finalize' && (
        <div>
          <h2 className="text-xl font-bold mb-4">Finalize Your Character</h2>
          <table className="w-full border mb-4">
            <tbody>
              {Object.entries(editData).map(([k, v]) => (
                <tr key={k}>
                  <td className="border px-2 py-1 font-semibold">{k}</td>
                  <td className="border px-2 py-1">
                    <input
                      className="w-full border p-1 rounded"
                      value={v}
                      onChange={e => setEditData({ ...editData, [k]: e.target.value })}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex justify-between">
            <button className="bg-gray-500 text-white p-2 rounded" onClick={discardChanges}>Discard Changes</button>
            <button className="bg-green-600 text-white p-2 rounded" onClick={saveCharacter}>Save Character</button>
          </div>
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
