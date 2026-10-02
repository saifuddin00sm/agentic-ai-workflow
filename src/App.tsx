import { useState } from 'react'

function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'architecture' | 'demo' | 'extending'>('overview')
  const [mockRunning, setMockRunning] = useState(false)
  const [mockStep, setMockStep] = useState(0)

  const pipelineSteps = [
    { name: 'PlannerAgent', icon: '📋', desc: 'Decomposes query into research tasks', status: 'idle' },
    { name: 'ResearchAgents', icon: '🔍', desc: 'Parallel tool-based research (Wikipedia, GDELT, SEC, Stocks)', status: 'idle' },
    { name: 'AnalystAgent', icon: '🧠', desc: 'Synthesizes findings into insights & risks', status: 'idle' },
    { name: 'WriterAgent', icon: '✍️', desc: 'Produces structured report with citations', status: 'idle' },
    { name: 'ValidatorAgent', icon: '✅', desc: 'Adversarial quality check, triggers revision if needed', status: 'idle' },
  ]

  const runMockDemo = () => {
    setMockRunning(true)
    setMockStep(0)
    const steps = [0, 1, 2, 3, 4, 5]
    steps.forEach((step, i) => {
      setTimeout(() => {
        setMockStep(step)
        if (step === 5) {
          setTimeout(() => setMockRunning(false), 2000)
        }
      }, (i + 1) * 800)
    })
  }

  const getStatusColor = (index: number) => {
    if (mockStep > index) return 'text-green-400'
    if (mockStep === index) return 'text-blue-400 animate-pulse'
    return 'text-gray-500'
  }

  const getStatusIcon = (index: number) => {
    if (mockStep > index) return '✓'
    if (mockStep === index) return '▶'
    return '○'
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🔬</span>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                AgentFlow
              </h1>
              <p className="text-xs text-gray-500">Multi-Agent Research & Analysis</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="px-3 py-1 text-xs bg-green-900/50 text-green-400 rounded-full border border-green-800">
              Python 3.11+
            </span>
            <span className="px-3 py-1 text-xs bg-purple-900/50 text-purple-400 rounded-full border border-purple-800">
              Demo Ready
            </span>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Multi-Agent Research Pipeline
            </span>
          </h2>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            Specialized agents plan, research, analyze, write, and validate — with structured outputs 
            at every stage, real API tools, graceful degradation, and a live event stream.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap justify-center gap-4 mb-16">
          <button
            onClick={runMockDemo}
            disabled={mockRunning}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-wait rounded-lg font-medium transition-all flex items-center gap-2"
          >
            {mockRunning ? '⏳ Running...' : '🚀 Run Mock Demo'}
          </button>
          <a
            href="https://github.com"
            className="px-6 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg font-medium transition-all border border-gray-700"
          >
            📦 View Source
          </a>
        </div>

        {/* Pipeline Visualization */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-16">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>⚡</span> Pipeline Stages
          </h3>
          <div className="space-y-3">
            {pipelineSteps.map((step, i) => (
              <div
                key={step.name}
                className={`flex items-center gap-4 p-3 rounded-lg transition-all ${
                  mockStep === i ? 'bg-blue-950/50 border border-blue-800' : 'bg-gray-800/50'
                }`}
              >
                <span className={`text-xl ${getStatusColor(i)}`}>
                  {getStatusIcon(i)}
                </span>
                <span className="text-2xl">{step.icon}</span>
                <div className="flex-1">
                  <div className="font-mono text-sm font-medium">{step.name}</div>
                  <div className="text-xs text-gray-500">{step.desc}</div>
                </div>
                {mockStep > i && (
                  <span className="text-xs text-green-400 bg-green-900/30 px-2 py-1 rounded">
                    complete
                  </span>
                )}
                {mockStep === i && (
                  <span className="text-xs text-blue-400 bg-blue-900/30 px-2 py-1 rounded animate-pulse">
                    running...
                  </span>
                )}
              </div>
            ))}
          </div>
          {mockStep >= 5 && (
            <div className="mt-4 p-3 bg-green-950/30 border border-green-800 rounded-lg text-center">
              <span className="text-green-400 font-medium">🏁 Pipeline completed successfully</span>
              <p className="text-xs text-gray-400 mt-1">
                Report generated with 12 citations, 5 sections, validation score: 0.92
              </p>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <div className="flex gap-1 bg-gray-900 rounded-lg p-1 w-fit">
            {(['overview', 'architecture', 'demo', 'extending'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  activeTab === tab
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <h3 className="text-xl font-bold">Key Features</h3>
              <div className="grid md:grid-cols-2 gap-4">
                {[
                  { icon: '🤖', title: '5 Specialized Agents', desc: 'Generic base class, zero copy-paste. Planner, Researcher, Analyst, Writer, Validator.' },
                  { icon: '🔧', title: '5 Real API Tools', desc: 'Wikipedia, GDELT News, Yahoo Finance, SEC EDGAR, Tavily — with shared HTTP helper.' },
                  { icon: '📊', title: 'Live Event Stream', desc: 'AsyncIterator[PipelineEvent] for real-time progress. UI layers only consume events.' },
                  { icon: '🛡️', title: 'Structured Outputs', desc: 'Pydantic v2 models at every stage boundary. No free-form dicts between stages.' },
                  { icon: '🔄', title: 'Graceful Degradation', desc: 'Failed research tasks carry forward. Report discloses reduced coverage.' },
                  { icon: '✅', title: 'Validation Loop', desc: 'Validator checks citations. Writer revises on failure. One revision loop max.' },
                  { icon: '🧪', title: 'Mock Mode', desc: 'Full demo runs offline with MockLLMClient + scripted responses.' },
                  { icon: '💉', title: 'Fault Injection', desc: '--inject-failure news demonstrates error handling live.' },
                ].map(f => (
                  <div key={f.title} className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{f.icon}</span>
                      <span className="font-medium text-sm">{f.title}</span>
                    </div>
                    <p className="text-xs text-gray-400">{f.desc}</p>
                  </div>
                ))}
              </div>

              <h3 className="text-xl font-bold mt-8">Quick Start</h3>
              <div className="bg-gray-950 rounded-lg p-4 font-mono text-sm border border-gray-800">
                <div className="text-gray-500"># Install</div>
                <div className="text-green-400">$ pip install -e ".[dev]"</div>
                <div className="text-gray-500 mt-3"># Run mock demo (no API keys needed)</div>
                <div className="text-green-400">$ python -m apps.cli "Company due-diligence brief on Acme Corp" --mock</div>
                <div className="text-gray-500 mt-3"># Run live (requires ANTHROPIC_API_KEY)</div>
                <div className="text-green-400">$ python -m apps.cli "Company due-diligence brief on Tesla"</div>
                <div className="text-gray-500 mt-3"># Web demo</div>
                <div className="text-green-400">$ streamlit run apps/streamlit_app.py</div>
              </div>
            </div>
          )}

          {activeTab === 'architecture' && (
            <div className="space-y-6">
              <h3 className="text-xl font-bold">Architecture</h3>
              
              <div className="bg-gray-950 rounded-lg p-6 border border-gray-800">
                <pre className="text-xs text-gray-300 overflow-x-auto whitespace-pre">{`
  ┌─────────────────────────────────────────────────────────────┐
  │                        Pipeline                             │
  │                                                             │
  │  ┌──────────┐    ┌──────────────────────────────────┐      │
  │  │ Planner  │───▶│     ResearchAgents (parallel)    │      │
  │  │  Agent   │    │  ┌─────┐ ┌─────┐ ┌─────┐       │      │
  │  └──────────┘    │  │ R_1 │ │ R_2 │ │ R_N │       │      │
  │       │          │  └──┬──┘ └──┬──┘ └──┬──┘       │      │
  │       ▼          │     │       │       │           │      │
  │  ResearchPlan    │     ▼       ▼       ▼           │      │
  │                  │   Tools   Tools   Tools         │      │
  │                  └────────────┬────────────────────┘      │
  │                               │                            │
  │                               ▼                            │
  │                  ┌────────────────────┐                   │
  │                  │   AnalystAgent     │                   │
  │                  └─────────┬──────────┘                   │
  │                            │                              │
  │                            ▼                              │
  │                  ┌────────────────────┐                   │
  │                  │    WriterAgent     │◀─────┐           │
  │                  └─────────┬──────────┘      │           │
  │                            │                  │           │
  │                            ▼                  │           │
  │                  ┌────────────────────┐       │           │
  │                  │  ValidatorAgent    │───────┘           │
  │                  └─────────┬──────────┘  (if fail)        │
  │                            │                              │
  │                            ▼                              │
  │                     FinalReport                           │
  └─────────────────────────────────────────────────────────────┘
                `}</pre>
              </div>

              <h3 className="text-xl font-bold">Design Principles</h3>
              <div className="space-y-3">
                {[
                  'Single Agent base class — all 5 agents reuse the same tool-use loop',
                  'Pydantic v2 contracts — every stage input/output is a validated model',
                  'Event-driven UI — core pipeline has ZERO UI/CLI imports',
                  'LLM provider behind protocol — swap Anthropic for any provider',
                  'Centralized resilience — one retry decorator, one timeout utility',
                  'Tool registry — adding a tool = one file + one registry line',
                ].map((p, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-gray-800/30 rounded-lg">
                    <span className="text-blue-400 font-mono text-sm">{i + 1}.</span>
                    <span className="text-sm text-gray-300">{p}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'demo' && (
            <div className="space-y-6">
              <h3 className="text-xl font-bold">Live Demo Scenarios</h3>
              
              <div className="space-y-4">
                <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-green-400">●</span>
                    <span className="font-medium">Scenario 1: Happy Path</span>
                  </div>
                  <code className="text-xs text-gray-400 bg-gray-950 px-3 py-2 rounded block">
                    python -m apps.cli "Company due-diligence brief on Acme Corp" --mock
                  </code>
                  <p className="text-xs text-gray-500 mt-2">
                    Full pipeline completes with a rendered report. All stages succeed.
                  </p>
                </div>

                <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-yellow-400">●</span>
                    <span className="font-medium">Scenario 2: Injected Tool Failure</span>
                  </div>
                  <code className="text-xs text-gray-400 bg-gray-950 px-3 py-2 rounded block">
                    python -m apps.cli "Company due-diligence brief on Acme Corp" --mock --inject-failure news
                  </code>
                  <p className="text-xs text-gray-500 mt-2">
                    News tool fails. Report is flagged as degraded but still completes with available data.
                  </p>
                </div>

                <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-blue-400">●</span>
                    <span className="font-medium">Scenario 3: Schema Repair</span>
                  </div>
                  <code className="text-xs text-gray-400 bg-gray-950 px-3 py-2 rounded block">
                    # Built into mock mode — agent's first output fails validation,
                    # repair turn fires, second attempt succeeds.
                  </code>
                  <p className="text-xs text-gray-500 mt-2">
                    Demonstrates the repair mechanism when LLM output doesn't match the Pydantic schema.
                  </p>
                </div>
              </div>

              <h3 className="text-xl font-bold mt-8">Event Stream Output</h3>
              <div className="bg-gray-950 rounded-lg p-4 font-mono text-xs border border-gray-800 max-h-64 overflow-y-auto">
                <div className="text-gray-500">▶ Stage: planner</div>
                <div className="text-green-400">✓ Stage: planner (245ms)</div>
                <div className="text-gray-500">▶ Stage: researcher_task_1</div>
                <div className="text-blue-400">  🔧 wikipedia(&#123;"query": "Acme Corp"&#125;)</div>
                <div className="text-green-400">  ✓ wikipedia → Acme Corp is a technology company...</div>
                <div className="text-blue-400">  🔧 news(&#123;"query": "Acme Corp recent"&#125;)</div>
                <div className="text-green-400">  ✓ news → Found 5 articles...</div>
                <div className="text-green-400">✓ Stage: researcher_task_1 (1230ms)</div>
                <div className="text-gray-500">▶ Stage: researcher_task_2</div>
                <div className="text-blue-400">  🔧 stocks(&#123;"ticker": "ACME"&#125;)</div>
                <div className="text-yellow-400">  ⚠ Tool failed: Connection timeout</div>
                <div className="text-green-400">✓ Stage: researcher_task_2 (890ms) [degraded]</div>
                <div className="text-yellow-400">  ⚠ Research degraded: 1/5 tasks failed</div>
                <div className="text-gray-500">▶ Stage: analyst</div>
                <div className="text-green-400">✓ Stage: analyst (1560ms)</div>
                <div className="text-gray-500">▶ Stage: writer</div>
                <div className="text-green-400">✓ Stage: writer (2100ms)</div>
                <div className="text-gray-500">▶ Stage: validator</div>
                <div className="text-green-400">✓ Stage: validator (890ms)</div>
                <div className="text-green-400 font-bold">🏁 Run completed (7230ms)</div>
              </div>
            </div>
          )}

          {activeTab === 'extending' && (
            <div className="space-y-6">
              <h3 className="text-xl font-bold">Extending AgentFlow</h3>
              
              <div>
                <h4 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <span className="text-blue-400">+</span> Adding a New Tool
                </h4>
                <div className="bg-gray-950 rounded-lg p-4 font-mono text-xs border border-gray-800 overflow-x-auto">
                  <div className="text-gray-500"># src/agentflow/tools/my_tool.py</div>
                  <div className="text-purple-400">from</div>
                  <div> pydantic <span className="text-purple-400">import</span> BaseModel, Field</div>
                  <div className="text-purple-400">from</div>
                  <div> agentflow.tools <span className="text-purple-400">import</span> Tool, ToolResult, http_get</div>
                  <div className="mt-3"></div>
                  <div><span className="text-blue-400">class</span> <span className="text-green-400">MyInput</span>(BaseModel):</div>
                  <div>    query: str = Field(description=<span className="text-yellow-300">"Search query"</span>)</div>
                  <div className="mt-3"></div>
                  <div><span className="text-blue-400">class</span> <span className="text-green-400">MyTool</span>(Tool[MyInput]):</div>
                  <div>    name = <span className="text-yellow-300">"my_tool"</span></div>
                  <div>    description = <span className="text-yellow-300">"Does something useful"</span></div>
                  <div>    input_model = MyInput</div>
                  <div className="mt-2"></div>
                  <div>    <span className="text-blue-400">async def</span> <span className="text-green-400">run</span>(self, input: MyInput) {'->'} ToolResult:</div>
                  <div>        resp = <span className="text-blue-400">await</span> http_get(<span className="text-yellow-300">"https://api.example.com"</span>, params=&#123;"q": input.query&#125;)</div>
                  <div>        <span className="text-blue-400">return</span> ToolResult(content=resp.text[:4000])</div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Then add one line to <code className="text-blue-400">tools/registry.py</code>: <code className="text-gray-400">registry.register(MyTool())</code>
                </p>
              </div>

              <div>
                <h4 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <span className="text-blue-400">+</span> Adding a New Agent
                </h4>
                <div className="bg-gray-950 rounded-lg p-4 font-mono text-xs border border-gray-800 overflow-x-auto">
                  <div><span className="text-blue-400">from</span> agentflow.agents <span className="text-blue-400">import</span> Agent, load_prompt</div>
                  <div></div>
                  <div><span className="text-blue-400">class</span> <span className="text-green-400">MyAgent</span>(Agent[MyInput, MyOutput]):</div>
                  <div>    <span className="text-blue-400">def</span> <span className="text-green-400">__init__</span>(self, **kwargs):</div>
                  <div>        super().__init__(</div>
                  <div>            name=<span className="text-yellow-300">"my_agent"</span>,</div>
                  <div>            system_prompt=load_prompt(<span className="text-yellow-300">"my_agent"</span>),</div>
                  <div>            input_model=MyInput,</div>
                  <div>            output_model=MyOutput,</div>
                  <div>            **kwargs,</div>
                  <div>        )</div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Create a prompt file at <code className="text-blue-400">prompts/my_agent.md</code> and you're done.
                </p>
              </div>

              <div>
                <h4 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <span className="text-blue-400">+</span> Swapping LLM Provider
                </h4>
                <div className="bg-gray-950 rounded-lg p-4 font-mono text-xs border border-gray-800 overflow-x-auto">
                  <div><span className="text-blue-400">from</span> agentflow.llm <span className="text-blue-400">import</span> LLMClient, LLMResponse, LLMMessage, ToolDefinition</div>
                  <div></div>
                  <div><span className="text-blue-400">class</span> <span className="text-green-400">OpenAIClient</span>:</div>
                  <div>    <span className="text-blue-400">async def</span> <span className="text-green-400">complete</span>(</div>
                  <div>        self, *, system: str, messages: list[LLMMessage],</div>
                  <div>        tools: list[ToolDefinition] | None = None,</div>
                  <div>        max_tokens: int = 4096,</div>
                  <div>    ) -&gt; LLMResponse:</div>
                  <div>        <span className="text-gray-500"># Implement OpenAI API call</span></div>
                  <div>        ...</div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Any class implementing the <code className="text-blue-400">LLMClient</code> protocol works. No changes to agents or pipeline needed.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Tech Stack */}
        <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { name: 'Python 3.11+', desc: 'async-first' },
            { name: 'Pydantic v2', desc: 'validated contracts' },
            { name: 'Anthropic SDK', desc: 'Claude tool use' },
            { name: 'httpx', desc: 'async HTTP' },
            { name: 'Typer + Rich', desc: 'CLI + live UI' },
            { name: 'Streamlit', desc: 'web demo' },
            { name: 'pytest + respx', desc: 'tested' },
            { name: 'ruff + mypy', desc: 'strict typing' },
          ].map(t => (
            <div key={t.name} className="p-3 bg-gray-900 rounded-lg border border-gray-800 text-center">
              <div className="font-mono text-sm font-medium text-blue-400">{t.name}</div>
              <div className="text-xs text-gray-500">{t.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-16">
        <div className="max-w-6xl mx-auto px-6 py-8 text-center text-sm text-gray-500">
          <p>AgentFlow — Built for demo reliability. Every stage boundary uses validated structured outputs.</p>
          <p className="mt-2 text-xs">
            No frameworks (LangChain, CrewAI, etc.). Plain SDK + own orchestration.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
