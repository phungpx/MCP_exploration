import React, { useState } from 'react';
import { Database, Cloud, FileText, BarChart, Settings, CheckCircle, Layers, ArrowRight, Code } from 'lucide-react';

const ArchitectureDiagram = () => {
    const [activeLayer, setActiveLayer] = useState('all');

    const LayerCard = ({ title, icon: Icon, color, items, layer }) => {
        const isActive = activeLayer === 'all' || activeLayer === layer;

        return (
            <div
                className={`bg-white rounded-lg shadow-md p-4 border-2 transition-all ${isActive ? `border-${color}-500` : 'border-gray-200 opacity-40'
                    }`}
                onClick={() => setActiveLayer(layer)}
            >
                <div className={`flex items-center gap-2 mb-3 text-${color}-700`}>
                    <Icon size={20} />
                    <h3 className="font-bold">{title}</h3>
                </div>
                <ul className="space-y-1 text-sm">
                    {items.map((item, idx) => (
                        <li key={idx} className="text-gray-700">
                            • {item}
                        </li>
                    ))}
                </ul>
            </div>
        );
    };

    const FlowArrow = () => (
        <div className="flex justify-center my-2">
            <ArrowRight className="text-gray-400" size={24} />
        </div>
    );

    return (
        <div className="w-full max-w-7xl mx-auto p-6 bg-gradient-to-br from-gray-50 to-blue-50">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg mb-6">
                <h1 className="text-3xl font-bold mb-2">Refactored Architecture</h1>
                <p className="text-blue-100">Modular, maintainable, and scalable design</p>
            </div>

            {/* Layer Filter */}
            <div className="bg-white rounded-lg shadow-md p-4 mb-6">
                <h3 className="font-bold text-gray-800 mb-3">View Layer:</h3>
                <div className="flex gap-2 flex-wrap">
                    {[
                        { id: 'all', label: 'All Layers', color: 'gray' },
                        { id: 'config', label: 'Configuration', color: 'blue' },
                        { id: 'clients', label: 'Clients', color: 'green' },
                        { id: 'models', label: 'Models', color: 'purple' },
                        { id: 'services', label: 'Services', color: 'orange' },
                        { id: 'utils', label: 'Utils', color: 'pink' },
                    ].map(layer => (
                        <button
                            key={layer.id}
                            onClick={() => setActiveLayer(layer.id)}
                            className={`px-4 py-2 rounded-lg font-semibold transition-all ${activeLayer === layer.id
                                ? `bg-${layer.color}-500 text-white`
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                }`}
                        >
                            {layer.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Architecture Layers */}
            <div className="space-y-4">
                {/* Entry Point */}
                <div className="bg-gradient-to-r from-indigo-100 to-indigo-200 p-4 rounded-lg border-2 border-indigo-400">
                    <div className="flex items-center gap-3">
                        <Code className="text-indigo-700" size={28} />
                        <div>
                            <h2 className="text-xl font-bold text-indigo-900">Entry Point</h2>
                            <p className="text-indigo-700 text-sm">main.py - BedrockBatchOptimizer</p>
                        </div>
                    </div>
                </div>

                <FlowArrow />

                {/* Configuration Layer */}
                <div className="grid md:grid-cols-3 gap-4">
                    <LayerCard
                        title="Configuration Layer"
                        icon={Settings}
                        color="blue"
                        layer="config"
                        items={[
                            'BedrockConfig - AWS settings',
                            'ModelRegistry - Model ID mapping',
                            'PricingConfig - Cost rates',
                        ]}
                    />

                    <LayerCard
                        title="Client Layer"
                        icon={Cloud}
                        color="green"
                        layer="clients"
                        items={[
                            'BedrockClient - AWS wrapper',
                            'Async aiobotocore session',
                            'create_invocation_job()',
                            'get_job_status()',
                        ]}
                    />

                    <LayerCard
                        title="Models Layer"
                        icon={Database}
                        color="purple"
                        layer="models"
                        items={[
                            'BatchRequest - Request data',
                            'BatchJob - Job metadata',
                            'BatchMetrics - Performance',
                            'CostComparison - Pricing',
                        ]}
                    />
                </div>

                <FlowArrow />

                {/* Services Layer */}
                <div className="bg-orange-50 border-2 border-orange-300 rounded-lg p-4">
                    <h2 className="text-xl font-bold text-orange-900 mb-4 flex items-center gap-2">
                        <Layers size={24} />
                        Services Layer - Core Business Logic
                    </h2>

                    <div className="grid md:grid-cols-3 gap-4">
                        <div className="bg-white p-4 rounded-lg shadow">
                            <h3 className="font-bold text-orange-800 mb-2">BatchService</h3>
                            <ul className="text-sm text-gray-700 space-y-1">
                                <li>✓ create_batch_requests()</li>
                                <li>✓ generate_jsonl()</li>
                                <li>✓ create_job()</li>
                            </ul>
                        </div>

                        <div className="bg-white p-4 rounded-lg shadow">
                            <h3 className="font-bold text-orange-800 mb-2">MonitoringService</h3>
                            <ul className="text-sm text-gray-700 space-y-1">
                                <li>✓ get_job_status()</li>
                                <li>✓ poll_until_complete()</li>
                                <li>✓ Status callbacks</li>
                            </ul>
                        </div>

                        <div className="bg-white p-4 rounded-lg shadow">
                            <h3 className="font-bold text-orange-800 mb-2">AnalysisService</h3>
                            <ul className="text-sm text-gray-700 space-y-1">
                                <li>✓ calculate_cost_comparison()</li>
                                <li>✓ analyze_batch_config()</li>
                                <li>✓ Recommendations</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <FlowArrow />

                {/* Utils Layer */}
                <LayerCard
                    title="Utilities Layer"
                    icon={FileText}
                    color="pink"
                    layer="utils"
                    items={[
                        'OutputFormatter - Console output',
                        'print_cost_comparison()',
                        'print_recommendations()',
                        'print_job_status()',
                    ]}
                />

                <FlowArrow />

                {/* Output */}
                <div className="bg-gradient-to-r from-green-100 to-green-200 p-4 rounded-lg border-2 border-green-400">
                    <div className="flex items-center gap-3">
                        <CheckCircle className="text-green-700" size={28} />
                        <div>
                            <h2 className="text-xl font-bold text-green-900">Output</h2>
                            <p className="text-green-700 text-sm">Cost analysis, recommendations, job monitoring</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Data Flow */}
            <div className="mt-8 bg-white rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <BarChart size={24} />
                    Data Flow Diagram
                </h2>

                <div className="space-y-3">
                    <div className="flex items-center gap-4">
                        <div className="bg-blue-100 px-4 py-2 rounded font-semibold text-blue-900 min-w-40">
                            1. User Request
                        </div>
                        <ArrowRight className="text-gray-400" />
                        <div className="bg-gray-100 px-4 py-2 rounded flex-1 text-sm">
                            main.py receives test cases + S3 URIs
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="bg-purple-100 px-4 py-2 rounded font-semibold text-purple-900 min-w-40">
                            2. Data Modeling
                        </div>
                        <ArrowRight className="text-gray-400" />
                        <div className="bg-gray-100 px-4 py-2 rounded flex-1 text-sm">
                            BatchRequest objects created from test cases
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="bg-orange-100 px-4 py-2 rounded font-semibold text-orange-900 min-w-40">
                            3. JSONL Generation
                        </div>
                        <ArrowRight className="text-gray-400" />
                        <div className="bg-gray-100 px-4 py-2 rounded flex-1 text-sm">
                            BatchService.generate_jsonl() converts to Bedrock format
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="bg-green-100 px-4 py-2 rounded font-semibold text-green-900 min-w-40">
                            4. Job Creation
                        </div>
                        <ArrowRight className="text-gray-400" />
                        <div className="bg-gray-100 px-4 py-2 rounded flex-1 text-sm">
                            BedrockClient.create_invocation_job() → AWS Bedrock API
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="bg-yellow-100 px-4 py-2 rounded font-semibold text-yellow-900 min-w-40">
                            5. Monitoring
                        </div>
                        <ArrowRight className="text-gray-400" />
                        <div className="bg-gray-100 px-4 py-2 rounded flex-1 text-sm">
                            MonitoringService.poll_until_complete() tracks status
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="bg-pink-100 px-4 py-2 rounded font-semibold text-pink-900 min-w-40">
                            6. Analysis
                        </div>
                        <ArrowRight className="text-gray-400" />
                        <div className="bg-gray-100 px-4 py-2 rounded flex-1 text-sm">
                            AnalysisService calculates costs & recommendations
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="bg-indigo-100 px-4 py-2 rounded font-semibold text-indigo-900 min-w-40">
                            7. Output
                        </div>
                        <ArrowRight className="text-gray-400" />
                        <div className="bg-gray-100 px-4 py-2 rounded flex-1 text-sm">
                            OutputFormatter displays formatted results
                        </div>
                    </div>
                </div>
            </div>

            {/* Benefits */}
            <div className="mt-8 grid md:grid-cols-2 gap-4">
                <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
                    <h3 className="font-bold text-green-900 mb-2">✓ Benefits of Refactoring</h3>
                    <ul className="text-green-800 text-sm space-y-1">
                        <li>• Single Responsibility Principle</li>
                        <li>• Easy to test each component</li>
                        <li>• Modular and reusable code</li>
                        <li>• Clear separation of concerns</li>
                        <li>• Easier to maintain and extend</li>
                    </ul>
                </div>

                <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                    <h3 className="font-bold text-blue-900 mb-2">📁 File Structure</h3>
                    <pre className="text-blue-800 text-xs font-mono">
                        {`bedrock_batch_optimizer/
├── config/
│   └── settings.py
├── clients/
│   └── bedrock_client.py
├── models/
│   ├── batch_job.py
│   └── pricing.py
├── services/
│   ├── batch_service.py
│   ├── monitoring_service.py
│   └── analysis_service.py
├── utils/
│   └── formatters.py
├── main.py
└── examples/
    └── demo.py`}
                    </pre>
                </div>
            </div>

            {/* Key Design Patterns */}
            <div className="mt-8 bg-white rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-4">🎨 Design Patterns Used</h2>

                <div className="grid md:grid-cols-3 gap-4">
                    <div className="bg-purple-50 p-4 rounded-lg">
                        <h3 className="font-bold text-purple-900 mb-2">Service Pattern</h3>
                        <p className="text-sm text-purple-800">
                            Business logic separated into focused services (BatchService, MonitoringService, AnalysisService)
                        </p>
                    </div>

                    <div className="bg-blue-50 p-4 rounded-lg">
                        <h3 className="font-bold text-blue-900 mb-2">Repository Pattern</h3>
                        <p className="text-sm text-blue-800">
                            BedrockClient abstracts AWS API interactions, making it easy to swap implementations
                        </p>
                    </div>

                    <div className="bg-green-50 p-4 rounded-lg">
                        <h3 className="font-bold text-green-900 mb-2">Factory Pattern</h3>
                        <p className="text-sm text-green-800">
                            ModelRegistry creates appropriate model instances, CostComparison.calculate() factory method
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ArchitectureDiagram;
