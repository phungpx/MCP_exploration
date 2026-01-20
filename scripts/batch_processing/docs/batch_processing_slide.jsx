import React, { useState } from 'react';
import { FileText, Clock, CheckCircle, XCircle, AlertCircle, DollarSign, Layers } from 'lucide-react';

const BatchProcessingDiagram = () => {
    const [activeTab, setActiveTab] = useState('overview');

    const OverviewSection = () => (
        <div className="space-y-6">
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <h3 className="font-bold text-blue-900 mb-2">What is Batch Processing?</h3>
                <p className="text-blue-800">
                    Instead of sending requests one-by-one and waiting for immediate responses,
                    batch processing lets you submit multiple requests together for asynchronous processing.
                    Think of it like mailing multiple letters at once instead of making individual trips to the post office.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <div className="flex items-center gap-2 mb-2">
                        <DollarSign className="text-green-600" size={24} />
                        <h4 className="font-bold text-green-900">50% Cost Savings</h4>
                    </div>
                    <p className="text-green-800 text-sm">All batch requests are charged at half the standard API prices</p>
                </div>

                <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                    <div className="flex items-center gap-2 mb-2">
                        <Clock className="text-purple-600" size={24} />
                        <h4 className="font-bold text-purple-900">Fast Processing</h4>
                    </div>
                    <p className="text-purple-800 text-sm">Most batches complete within 1 hour</p>
                </div>

                <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                    <div className="flex items-center gap-2 mb-2">
                        <Layers className="text-orange-600" size={24} />
                        <h4 className="font-bold text-orange-900">Massive Scale</h4>
                    </div>
                    <p className="text-orange-800 text-sm">Up to 100,000 requests or 256 MB per batch</p>
                </div>

                <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
                    <div className="flex items-center gap-2 mb-2">
                        <FileText className="text-indigo-600" size={24} />
                        <h4 className="font-bold text-indigo-900">Full Feature Support</h4>
                    </div>
                    <p className="text-indigo-800 text-sm">Vision, tools, caching - everything works in batches</p>
                </div>
            </div>
        </div>
    );

    const FlowDiagram = () => (
        <div className="space-y-4">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Batch Processing Flow</h3>

            {/* Step 1 */}
            <div className="relative">
                <div className="bg-blue-100 border-l-4 border-blue-600 p-4 rounded-lg">
                    <div className="flex items-start gap-3">
                        <div
                            className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">
                            1</div>
                        <div className="flex-1">
                            <h4 className="font-bold text-blue-900 mb-2">Create Batch Request</h4>
                            <p className="text-blue-800 text-sm mb-2">Submit multiple requests with unique custom_id values</p>
                            <div className="bg-white p-3 rounded border border-blue-200 font-mono text-xs">
                                {`{
                        "requests": [
                        {
                        "custom_id": "request-1",
                        "params": {
                        "model": "claude-sonnet-4-5",
                        "messages": [...]
                        }
                        }
                        ]
                        }`}
                            </div>
                        </div>
                    </div>
                </div>
                <div className="flex justify-center my-2">
                    <div className="w-0.5 h-8 bg-gray-300"></div>
                </div>
            </div>

            {/* Step 2 */}
            <div className="relative">
                <div className="bg-yellow-100 border-l-4 border-yellow-600 p-4 rounded-lg">
                    <div className="flex items-start gap-3">
                        <div
                            className="bg-yellow-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">
                            2</div>
                        <div className="flex-1">
                            <h4 className="font-bold text-yellow-900 mb-2">Batch Created - Status: "in_progress"</h4>
                            <p className="text-yellow-800 text-sm mb-2">System assigns batch ID and begins asynchronous
                                processing</p>
                            <div className="bg-white p-3 rounded border border-yellow-200 font-mono text-xs">
                                {`{
                        "id": "msgbatch_01Hkc...",
                        "processing_status": "in_progress",
                        "request_counts": {
                        "processing": 2,
                        "succeeded": 0,
                        "errored": 0
                        }
                        }`}
                            </div>
                        </div>
                    </div>
                </div>
                <div className="flex justify-center my-2">
                    <div className="w-0.5 h-8 bg-gray-300"></div>
                </div>
            </div>

            {/* Step 3 */}
            <div className="relative">
                <div className="bg-purple-100 border-l-4 border-purple-600 p-4 rounded-lg">
                    <div className="flex items-start gap-3">
                        <div
                            className="bg-purple-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">
                            3</div>
                        <div className="flex-1">
                            <h4 className="font-bold text-purple-900 mb-2">Poll for Status</h4>
                            <p className="text-purple-800 text-sm mb-2">Check batch status periodically (recommended: every 60
                                seconds)</p>
                            <div className="grid grid-cols-2 gap-2 mt-3">
                                <div className="bg-white p-2 rounded border border-purple-200 text-xs">
                                    <span className="font-bold">Status Options:</span>
                                    <ul className="mt-1 space-y-1 text-purple-800">
                                        <li>• in_progress</li>
                                        <li>• canceling</li>
                                        <li>• ended</li>
                                    </ul>
                                </div>
                                <div className="bg-white p-2 rounded border border-purple-200 text-xs">
                                    <span className="font-bold">Time Limits:</span>
                                    <ul className="mt-1 space-y-1 text-purple-800">
                                        <li>• Most: &lt;1 hour</li>
                                        <li>• Max: 24 hours</li>
                                        <li>• Results: 29 days</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="flex justify-center my-2">
                    <div className="w-0.5 h-8 bg-gray-300"></div>
                </div>
            </div>

            {/* Step 4 */}
            <div className="relative">
                <div className="bg-green-100 border-l-4 border-green-600 p-4 rounded-lg">
                    <div className="flex items-start gap-3">
                        <div
                            className="bg-green-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">
                            4</div>
                        <div className="flex-1">
                            <h4 className="font-bold text-green-900 mb-2">Processing Complete - Status: "ended"</h4>
                            <p className="text-green-800 text-sm mb-2">Download results from results_url (.jsonl format)</p>
                            <div className="grid grid-cols-4 gap-2 mt-3">
                                <div className="bg-green-50 p-2 rounded border border-green-300 text-center">
                                    <CheckCircle className="mx-auto text-green-600 mb-1" size={20} />
                                    <span className="text-xs font-bold text-green-900">succeeded</span>
                                </div>
                                <div className="bg-red-50 p-2 rounded border border-red-300 text-center">
                                    <XCircle className="mx-auto text-red-600 mb-1" size={20} />
                                    <span className="text-xs font-bold text-red-900">errored</span>
                                </div>
                                <div className="bg-gray-50 p-2 rounded border border-gray-300 text-center">
                                    <AlertCircle className="mx-auto text-gray-600 mb-1" size={20} />
                                    <span className="text-xs font-bold text-gray-900">canceled</span>
                                </div>
                                <div className="bg-orange-50 p-2 rounded border border-orange-300 text-center">
                                    <Clock className="mx-auto text-orange-600 mb-1" size={20} />
                                    <span className="text-xs font-bold text-orange-900">expired</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const UseCases = () => (
        <div className="space-y-4">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Ideal Use Cases</h3>

            <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
                <h4 className="font-bold text-blue-900 mb-2">✓ GREAT FOR Batch Processing:</h4>
                <ul className="space-y-2 text-blue-800">
                    <li className="flex items-start gap-2">
                        <span className="text-blue-600 font-bold">•</span>
                        <span><strong>Large-scale evaluations:</strong> Testing 10,000 prompts against your model</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-blue-600 font-bold">•</span>
                        <span><strong>Content moderation:</strong> Analyzing thousands of user posts overnight</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-blue-600 font-bold">•</span>
                        <span><strong>Bulk generation:</strong> Creating product descriptions for entire catalog</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-blue-600 font-bold">•</span>
                        <span><strong>Data analysis:</strong> Summarizing customer feedback from thousands of surveys</span>
                    </li>
                </ul>
            </div>

            <div className="bg-gradient-to-r from-red-50 to-red-100 p-4 rounded-lg border border-red-200">
                <h4 className="font-bold text-red-900 mb-2">✗ NOT SUITABLE FOR:</h4>
                <ul className="space-y-2 text-red-800">
                    <li className="flex items-start gap-2">
                        <span className="text-red-600 font-bold">•</span>
                        <span><strong>Real-time chatbots:</strong> Users expect immediate responses</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-red-600 font-bold">•</span>
                        <span><strong>Interactive applications:</strong> Need instant feedback loops</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-red-600 font-bold">•</span>
                        <span><strong>Time-sensitive tasks:</strong> Results needed within seconds/minutes</span>
                    </li>
                </ul>
            </div>
        </div>
    );

    const KeyConcepts = () => (
        <div className="space-y-4">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Key Concepts to Understand</h3>

            <div className="space-y-3">
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h4 className="font-bold text-gray-900 mb-2">🔑 custom_id - Your Request Identifier</h4>
                    <p className="text-gray-700 text-sm mb-2">
                        Each request needs a unique ID that YOU define. This is critical because:
                    </p>
                    <ul className="text-sm text-gray-600 space-y-1 ml-4">
                        <li>• Results can return in ANY order (not guaranteed to match input order)</li>
                        <li>• You use custom_id to match results back to original requests</li>
                        <li>• Think of it like a tracking number for each package in your shipment</li>
                    </ul>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h4 className="font-bold text-gray-900 mb-2">📊 request_counts - Your Progress Dashboard</h4>
                    <p className="text-gray-700 text-sm mb-2">
                        Shows the current status of all requests in your batch:
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="bg-yellow-50 p-2 rounded">
                            <strong>processing:</strong> Still being worked on
                        </div>
                        <div className="bg-green-50 p-2 rounded">
                            <strong>succeeded:</strong> Completed successfully
                        </div>
                        <div className="bg-red-50 p-2 rounded">
                            <strong>errored:</strong> Failed (not billed)
                        </div>
                        <div className="bg-orange-50 p-2 rounded">
                            <strong>expired:</strong> Took &gt;24hrs (not billed)
                        </div>
                    </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h4 className="font-bold text-gray-900 mb-2">⚡ Prompt Caching Bonus</h4>
                    <p className="text-gray-700 text-sm mb-2">
                        You can combine batch processing with prompt caching for even bigger savings:
                    </p>
                    <ul className="text-sm text-gray-600 space-y-1 ml-4">
                        <li>• Batch discount: 50% off standard prices</li>
                        <li>• Cache hits: Additional 90% off cached tokens</li>
                        <li>• Combined: Can reduce costs by 95% for cached content!</li>
                        <li>• Cache hit rates typically range from 30% to 98%</li>
                    </ul>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h4 className="font-bold text-gray-900 mb-2">🔒 Privacy & Isolation</h4>
                    <p className="text-gray-700 text-sm">
                        Batches are workspace-scoped. Only API keys and users from the same workspace
                        can access the batch and its results. Results are available for 29 days after creation.
                    </p>
                </div>
            </div>
        </div>
    );

    return (
        <div className="w-full max-w-6xl mx-auto p-6 bg-gray-50">
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-lg mb-6">
                <h1 className="text-3xl font-bold mb-2">Claude Batch Processing API</h1>
                <p className="text-purple-100">Comprehensive Guide: Process thousands of requests at 50% cost</p>
            </div>

            <div className="bg-white rounded-lg shadow-md mb-6">
                <div className="flex border-b border-gray-200">
                    {[
                        { id: 'overview', label: 'Overview' },
                        { id: 'flow', label: 'Process Flow' },
                        { id: 'concepts', label: 'Key Concepts' },
                        { id: 'usecases', label: 'Use Cases' }
                    ].map(tab => (
                        <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                            className={`px-6 py-3 font-semibold transition-colors ${activeTab === tab.id
                                ? 'border-b-2 border-purple-600 text-purple-600'
                                : 'text-gray-600 hover:text-gray-800'
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                <div className="p-6">
                    {activeTab === 'overview' &&
                        <OverviewSection />}
                    {activeTab === 'flow' &&
                        <FlowDiagram />}
                    {activeTab === 'concepts' &&
                        <KeyConcepts />}
                    {activeTab === 'usecases' &&
                        <UseCases />}
                </div>
            </div>

            <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
                <h3 className="font-bold text-yellow-900 mb-2">💡 Pro Tip</h3>
                <p className="text-yellow-800 text-sm">
                    Always test your request format with the regular Messages API first!
                    Batch validation happens asynchronously, so catching errors early saves time.
                </p>
            </div>
        </div>
    );
};

export default BatchProcessingDiagram;
