import { useState } from "react";

export function App() {
  const [count, setCount] = useState(0);
  return (
    <main>
      <h1>React listo</h1>
      <button type="button" onClick={() => setCount((current) => current + 1)}>
        Incrementar: {count}
      </button>
    </main>
  );
}
