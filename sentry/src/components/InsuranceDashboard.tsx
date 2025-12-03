'use client';

import { useState } from 'react';
import { AnalysisResult } from '@/lib/types';

interface InsuranceDashboardProps {
    result: AnalysisResult | null;
    onBack: () => void;
}

interface InsuranceMetrics {
    premium: number;
    riskScore: number;
    policyType: 'Standard' | 'High Risk' | 'Premium' | 'Uninsurable';
    maxCoverage: number;
    deductible: number;
    factors: { name: string; impact: 'High' | 'Medium' | 'Low'; value: string }[];
}

export function InsuranceDashboard({ result, onBack }: InsuranceDashboardProps) {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [metrics, setMetrics] = useState<InsuranceMetrics | null>(null);

    const handleAnalyze = () => {
        setIsAnalyzing(true);
        // Mock analysis delay
        setTimeout(() => {
            // Generate mock data based on the input result (if available) or random
            const baseRisk = result?.summary?.averageRisk
                ? (result.summary.averageRisk > 75 ? 85 : result.summary.averageRisk > 50 ? 50 : 20)
                : Math.floor(Math.random() * 100);

            const calculatedRisk = Math.min(100, Math.max(0, baseRisk + (Math.random() * 10 - 5)));

            let policyType: InsuranceMetrics['policyType'] = 'Standard';
            if (calculatedRisk > 80) policyType = 'Uninsurable';
            else if (calculatedRisk > 60) policyType = 'High Risk';
            else if (calculatedRisk < 30) policyType = 'Premium';

            setMetrics({
                premium: Math.round(1000 + (calculatedRisk * 50)),
                riskScore: Math.round(calculatedRisk),
                policyType,
                maxCoverage: Math.round(1000000 - (calculatedRisk * 5000)),
                deductible: Math.round(5000 + (calculatedRisk * 100)),
                factors: [
                    { name: 'Historical Weather Patterns', impact: 'High', value: 'Volatile' },
                    { name: 'Soil Composition Quality', impact: 'Medium', value: 'Grade B' },
                    { name: 'Pest Infestation Probability', impact: 'High', value: `${Math.round(calculatedRisk * 0.8)}%` },
                    { name: 'Crop Yield Forecast', impact: 'Medium', value: 'Stable' },
                ]
            });
            setIsAnalyzing(false);
        }, 2000);
    };

    return (
        <div className="flex h-screen w-full flex-col bg-[#0f0f0f] text-white overflow-hidden font-sans">
            {/* Header */}
            <header className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 bg-[#141414] px-6">
                <div className="flex items-center gap-4">
                    <button
                        onClick={onBack}
                        className="flex items-center justify-center rounded-full p-2 text-white/50 hover:bg-white/5 hover:text-white transition-colors"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="m15 18-6-6 6-6" />
                        </svg>
                    </button>
                    <h1 className="text-lg font-bold uppercase tracking-wider">Insurance Risk Dashboard</h1>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-xs text-white/40 font-mono">
                        SESSION: {new Date().toLocaleDateString()}
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex flex-1 overflow-hidden">
                {/* Left Panel - Input Summary */}
                <div className="w-80 border-r border-white/10 bg-[#141414]/50 p-6 overflow-y-auto">
                    <h2 className="mb-6 text-xs font-bold uppercase tracking-[0.2em] text-white/40">Input Data Source</h2>

                    <div className="space-y-6">
                        <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                            <div className="mb-2 text-[10px] uppercase tracking-wider text-white/50">Analysis Model</div>
                            <div className="font-mono text-sm text-white">Agricultural Risk V2</div>
                        </div>

                        <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                            <div className="mb-2 text-[10px] uppercase tracking-wider text-white/50">Target Area</div>
                            <div className="font-mono text-sm text-white">
                                {result?.summary?.areaKm2 ? `${result.summary.areaKm2} km²` : 'N/A'}
                            </div>
                        </div>

                        <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                            <div className="mb-2 text-[10px] uppercase tracking-wider text-white/50">Detected Risks</div>
                            <div className="space-y-2">
                                <div className="flex justify-between text-xs font-mono">
                                    <span className="text-white/60">High Priority</span>
                                    <span className="text-red-400">{result?.summary?.highRiskCells || 0}</span>
                                </div>
                                <div className="flex justify-between text-xs font-mono">
                                    <span className="text-white/60">Medium Priority</span>
                                    <span className="text-orange-400">{result?.summary?.mediumRiskCells || 0}</span>
                                </div>
                            </div>
                        </div>

                        {!metrics && !isAnalyzing && (
                            <button
                                onClick={handleAnalyze}
                                className="w-full rounded bg-blue-600 py-3 text-xs font-bold uppercase tracking-widest text-white hover:bg-blue-500 transition-colors shadow-[0_0_20px_rgba(37,99,235,0.3)]"
                            >
                                Run Insurance Model
                            </button>
                        )}
                    </div>
                </div>

                {/* Center/Right Panel - Results */}
                <div className="flex-1 p-8 overflow-y-auto relative">
                    {/* Background Grid */}
                    <div
                        className="absolute inset-0 opacity-[0.02] pointer-events-none"
                        style={{
                            backgroundImage: `linear-gradient(to right, #ffffff 1px, transparent 1px), linear-gradient(to bottom, #ffffff 1px, transparent 1px)`,
                            backgroundSize: '40px 40px'
                        }}
                    />

                    {isAnalyzing ? (
                        <div className="flex h-full flex-col items-center justify-center space-y-4">
                            <div className="h-12 w-12 animate-spin rounded-full border-4 border-white/10 border-t-blue-500" />
                            <div className="text-sm font-mono uppercase tracking-widest text-blue-400 animate-pulse">
                                Processing Actuarial Models...
                            </div>
                        </div>
                    ) : metrics ? (
                        <div className="mx-auto max-w-5xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">

                            {/* Top Cards */}
                            <div className="grid grid-cols-4 gap-6">
                                <div className="col-span-1 rounded-xl border border-white/10 bg-[#1a1a1a] p-6 shadow-2xl">
                                    <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-white/40">Risk Score</div>
                                    <div className={`text-5xl font-bold ${metrics.riskScore > 75 ? 'text-red-500' :
                                        metrics.riskScore > 50 ? 'text-orange-500' : 'text-green-500'
                                        }`}>
                                        {metrics.riskScore}<span className="text-lg align-top opacity-50">/100</span>
                                    </div>
                                </div>

                                <div className="col-span-1 rounded-xl border border-white/10 bg-[#1a1a1a] p-6 shadow-2xl">
                                    <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-white/40">Monthly Premium</div>
                                    <div className="text-4xl font-bold text-white">
                                        <span className="text-lg align-top opacity-50">$</span>{metrics.premium.toLocaleString()}
                                    </div>
                                </div>

                                <div className="col-span-1 rounded-xl border border-white/10 bg-[#1a1a1a] p-6 shadow-2xl">
                                    <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-white/40">Policy Status</div>
                                    <div className={`text-2xl font-bold uppercase tracking-wide ${metrics.policyType === 'Uninsurable' ? 'text-red-500' : 'text-blue-400'
                                        }`}>
                                        {metrics.policyType}
                                    </div>
                                </div>

                                <div className="col-span-1 rounded-xl border border-white/10 bg-[#1a1a1a] p-6 shadow-2xl">
                                    <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-white/40">Max Coverage</div>
                                    <div className="text-3xl font-bold text-white">
                                        <span className="text-lg align-top opacity-50">$</span>{(metrics.maxCoverage / 1000000).toFixed(1)}M
                                    </div>
                                </div>
                            </div>

                            {/* Detailed Breakdown */}
                            <div className="grid grid-cols-3 gap-6">
                                {/* Risk Factors */}
                                <div className="col-span-2 rounded-xl border border-white/10 bg-[#1a1a1a] p-6">
                                    <h3 className="mb-6 text-xs font-bold uppercase tracking-[0.2em] text-white/60">Risk Factor Analysis</h3>
                                    <div className="space-y-4">
                                        {metrics.factors.map((factor, i) => (
                                            <div key={i} className="flex items-center justify-between border-b border-white/5 pb-4 last:border-0 last:pb-0">
                                                <div className="flex items-center gap-3">
                                                    <div className={`h-2 w-2 rounded-full ${factor.impact === 'High' ? 'bg-red-500' :
                                                        factor.impact === 'Medium' ? 'bg-orange-500' : 'bg-blue-500'
                                                        }`} />
                                                    <span className="text-sm font-medium text-white/90">{factor.name}</span>
                                                </div>
                                                <div className="flex items-center gap-6">
                                                    <span className="text-xs font-mono text-white/50 uppercase">{factor.impact} Impact</span>
                                                    <span className="text-sm font-mono font-bold text-white w-24 text-right">{factor.value}</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Recommendations */}
                                <div className="col-span-1 rounded-xl border border-white/10 bg-[#1a1a1a] p-6">
                                    <h3 className="mb-6 text-xs font-bold uppercase tracking-[0.2em] text-white/60">Recommendations</h3>
                                    <ul className="space-y-4">
                                        <li className="flex gap-3 text-sm text-white/70">
                                            <span className="text-blue-400">01.</span>
                                            Implement advanced irrigation systems to mitigate drought risk.
                                        </li>
                                        <li className="flex gap-3 text-sm text-white/70">
                                            <span className="text-blue-400">02.</span>
                                            Increase pest monitoring frequency in Sector 4.
                                        </li>
                                        <li className="flex gap-3 text-sm text-white/70">
                                            <span className="text-blue-400">03.</span>
                                            Review soil enrichment plan for next quarter.
                                        </li>
                                    </ul>

                                    <button className="mt-8 w-full rounded border border-white/20 bg-white/5 py-3 text-xs font-bold uppercase tracking-widest text-white hover:bg-white/10 transition-colors">
                                        Download Full Report
                                    </button>
                                </div>
                            </div>

                        </div>
                    ) : (
                        <div className="flex h-full flex-col items-center justify-center text-white/30">
                            <div className="mb-4 rounded-full border border-white/10 bg-white/5 p-6">
                                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                                    <path d="m9 12 2 2 4-4" />
                                </svg>
                            </div>
                            <p className="text-sm uppercase tracking-widest">Ready to Analyze</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
