'use client';

import { useState } from 'react';
import { AnalysisResult, LocationSelection } from '@/lib/types';
import { runInsuranceAnalysis, InsuranceAnalysisResponse, generateInsurancePDF, PDFRequest } from '@/lib/api';

interface InsuranceDashboardProps {
    result: AnalysisResult | null;
    location: LocationSelection | null;
    onBack: () => void;
}

export function InsuranceDashboard({ result, location, onBack }: InsuranceDashboardProps) {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const [metrics, setMetrics] = useState<InsuranceAnalysisResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [analyzedLocation, setAnalyzedLocation] = useState<{ lat: number; lon: number } | null>(null);

    const handleAnalyze = async () => {
        if (!result?.summary) return;

        setIsAnalyzing(true);
        setError(null);

        try {
            const baseRisk = result.summary.averageRisk || 50;
            // Use actual location from props if available, otherwise fallback
            let lat = 38.5;
            let lon = -98.0;

            if (location) {
                if (location.type === 'custom' && location.polygon && location.polygon.length > 0) {
                    // Calculate centroid
                    lat = location.polygon.reduce((sum, p) => sum + p.lat, 0) / location.polygon.length;
                    lon = location.polygon.reduce((sum, p) => sum + p.lng, 0) / location.polygon.length;
                } else if (location.bounds) {
                    lat = (location.bounds.southWest.lat + location.bounds.northEast.lat) / 2;
                    lon = (location.bounds.southWest.lng + location.bounds.northEast.lng) / 2;
                }
            }

            const requestData = {
                agri_risk_score: baseRisk,
                lat: lat,
                lon: lon
            };

            const data = await runInsuranceAnalysis(requestData);
            setMetrics(data);
            setAnalyzedLocation({ lat, lon });
        } catch (err) {
            console.error('Insurance analysis failed:', err);
            setError('Failed to run insurance analysis. Please try again.');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleDownloadPDF = async () => {
        if (!metrics || !analyzedLocation) return;

        setIsDownloading(true);
        try {
            const pdfData: PDFRequest = {
                farmName: location?.parkName || "My Farm",
                lat: analyzedLocation.lat,
                lon: analyzedLocation.lon,
                areaKm2: result?.summary?.areaKm2 || 0,
                cropType: "Mixed", // TODO: Get from params if available
                risk_score: metrics.risk_score,
                policy_type: metrics.policy_type,
                max_coverage: metrics.max_coverage,
                deductible: metrics.deductible,
                premium: metrics.premium,
                coverage_period: metrics.coverage_period || "12 Months",
                factors: metrics.factors,
                recommended_actions: metrics.recommended_actions || [],
                polygon: location?.type === 'custom' ? location.polygon : undefined
            };

            const blob = await generateInsurancePDF(pdfData);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `insurance_proposal_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            console.error('PDF download failed:', err);
            setError('Failed to generate PDF report.');
        } finally {
            setIsDownloading(false);
        }
    };

    // Generate risk zone data based on actual analysis results
    const riskZoneLabels = result?.summary ?
        ['Zone A', 'Zone B', 'Zone C', 'Zone D', 'Zone E', 'Zone F', 'Zone G', 'Zone H', 'Zone I', 'Zone J', 'Zone K'] :
        ['Sector 1', 'Sector 2', 'Sector 3', 'Sector 4', 'Sector 5', 'Sector 6', 'Sector 7', 'Sector 8', 'Sector 9', 'Sector 10', 'Sector 11'];

    // Generate values based on risk distribution or use defaults
    const riskZoneValues = result?.summary ?
        Array.from({ length: 11 }, (_, i) => Math.floor((result.summary?.averageRisk || 50) * (0.8 + Math.random() * 0.4))) :
        [45, 32, 58, 42, 67, 51, 73, 82, 89, 95, 78];

    return (
        <div className="flex h-screen w-full flex-col bg-[#0a0a0a] text-white overflow-hidden font-sans">
            {/* Top Bar with Risk Zones Chart */}
            <div className="flex h-32 shrink-0 items-center border-b border-white/[0.08] bg-[#0f0f0f] px-8">
                <div className="flex items-center gap-6 mr-12">
                    <button
                        onClick={onBack}
                        className="flex items-center justify-center rounded p-1.5 text-white/40 hover:bg-white/5 hover:text-white transition-colors"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="m15 18-6-6 6-6" />
                        </svg>
                    </button>
                    {/* Sentry Logo */}
                    <img src="/sentry_logo.svg" alt="Sentry" className="h-8 w-8" />
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-[#d4af37]" />
                        <span className="text-xs uppercase tracking-wider text-white/60 font-medium">Risk Zones</span>
                    </div>
                </div>

                {/* Mini Bar Chart - Risk Distribution */}
                <div className="flex items-end gap-[3px] h-16">
                    {riskZoneValues.map((val, i) => (
                        <div key={i} className="flex flex-col items-center gap-1 group">
                            <div
                                className="w-[18px] bg-gradient-to-t from-[#d4af37]/80 to-[#d4af37]/20 transition-all duration-300 group-hover:from-[#d4af37] group-hover:to-[#d4af37]/40"
                                style={{ height: `${(val / 100) * 60}px` }}
                            />
                            <span className="text-[8px] text-white/30 font-mono">{riskZoneLabels[i]}</span>
                        </div>
                    ))}
                </div>

                <div className="ml-auto flex items-center gap-6">
                    {analyzedLocation && (
                        <div className="text-[10px] text-white/40 font-mono">
                            Location: {analyzedLocation.lat.toFixed(2)}°, {analyzedLocation.lon.toFixed(2)}°
                        </div>
                    )}

                    {metrics && (
                        <button
                            onClick={handleDownloadPDF}
                            disabled={isDownloading}
                            className="flex items-center gap-2 rounded border border-[#d4af37]/30 bg-[#d4af37]/10 px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-[#d4af37] hover:bg-[#d4af37]/20 disabled:opacity-50 transition-all"
                        >
                            {isDownloading ? (
                                <>
                                    <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#d4af37] border-t-transparent" />
                                    <span>Generating...</span>
                                </>
                            ) : (
                                <>
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                        <polyline points="7 10 12 15 17 10" />
                                        <line x1="12" y1="15" x2="12" y2="3" />
                                    </svg>
                                    <span>Download Proposal</span>
                                </>
                            )}
                        </button>
                    )}

                    <div className="text-[10px] text-white/30 font-mono uppercase tracking-wider">
                        Agricultural Insurance Analytics
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <main className="flex flex-1 overflow-hidden">
                {/* Left Panel - Visualizations Grid */}
                <div className="flex-1 p-6 overflow-y-auto">
                    {!metrics && !isAnalyzing && (
                        <div className="flex h-full flex-col items-center justify-center">
                            <div className="mb-6 rounded-full border border-white/10 bg-white/5 p-8">
                                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="text-white/20">
                                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                                </svg>
                            </div>
                            <p className="text-sm uppercase tracking-[0.2em] text-white/30 mb-8">Ready to Analyze</p>
                            <button
                                onClick={handleAnalyze}
                                className="rounded bg-[#d4af37] px-8 py-3 text-xs font-bold uppercase tracking-[0.15em] text-black hover:bg-[#f4a460] transition-all duration-300 shadow-[0_0_30px_rgba(212,175,55,0.3)]"
                            >
                                Run Insurance Analysis
                            </button>
                            {error && (
                                <div className="mt-6 rounded border border-red-500/30 bg-red-500/10 px-6 py-3 text-xs text-red-300">
                                    {error}
                                </div>
                            )}
                        </div>
                    )}

                    {isAnalyzing && (
                        <div className="flex h-full flex-col items-center justify-center space-y-6">
                            <div className="h-16 w-16 animate-spin rounded-full border-4 border-white/10 border-t-[#d4af37]" />
                            <div className="text-sm font-mono uppercase tracking-[0.2em] text-[#d4af37] animate-pulse">
                                Processing Actuarial Models...
                            </div>
                        </div>
                    )}

                    {metrics && (
                        <div className="grid grid-cols-2 gap-6 h-full">
                            {/* Loyalty / Risk Gauge */}
                            <div className="rounded-lg border border-white/[0.08] bg-[#0f0f0f] p-6 hover:border-white/[0.15] transition-all duration-300">
                                <div className="flex items-center gap-2 mb-6">
                                    <svg width="12" height="12" viewBox="0 0 12 12" className="text-white/60">
                                        <path d="M6 2L8 6L6 10L4 6Z" fill="currentColor" />
                                    </svg>
                                    <span className="text-[10px] uppercase tracking-[0.15em] text-white/60 font-medium">Coverage Score</span>
                                </div>

                                <div className="flex items-center justify-center h-48 relative">
                                    <svg width="200" height="200" viewBox="0 0 200 200" className="transform -rotate-90">
                                        {/* Background arc */}
                                        <circle cx="100" cy="100" r="70" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="2" />
                                        {/* Progress arc */}
                                        <circle
                                            cx="100"
                                            cy="100"
                                            r="70"
                                            fill="none"
                                            stroke="#d4af37"
                                            strokeWidth="2"
                                            strokeDasharray={`${(metrics.risk_score / 100) * 440} 440`}
                                            className="transition-all duration-1000"
                                        />
                                        {/* Inner circle */}
                                        <circle cx="100" cy="100" r="60" fill="none" stroke="rgba(212,175,55,0.2)" strokeWidth="1" />
                                    </svg>
                                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                                        <div className="text-4xl font-bold text-[#d4af37]">{metrics.risk_score}</div>
                                        <div className="text-[10px] text-white/40 uppercase tracking-wider mt-1">Risk Level</div>
                                    </div>
                                </div>

                                <div className="flex justify-between mt-6 text-[10px] font-mono">
                                    <span className="text-white/40">INITIAL</span>
                                    <span className="text-white/40">LOW</span>
                                    <span className="text-[#d4af37]">91%</span>
                                </div>
                            </div>

                            {/* Trend Chart */}
                            <div className="rounded-lg border border-white/[0.08] bg-[#0f0f0f] p-6 hover:border-white/[0.15] transition-all duration-300">
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-2">
                                        <svg width="12" height="12" viewBox="0 0 12 12" className="text-white/60">
                                            <path d="M2 10L5 4L8 7L10 2" stroke="currentColor" fill="none" strokeWidth="1.5" />
                                        </svg>
                                        <span className="text-[10px] uppercase tracking-[0.15em] text-white/60 font-medium">Trend</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-white/40">+</span>
                                        <span className="text-lg font-bold text-white">{metrics.risk_score}</span>
                                        <span className="text-[10px] text-white/40">%</span>
                                    </div>
                                </div>

                                <div className="relative h-48">
                                    <svg width="100%" height="100%" viewBox="0 0 300 180" preserveAspectRatio="none">
                                        {/* Grid lines */}
                                        <line x1="0" y1="45" x2="300" y2="45" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
                                        <line x1="0" y1="90" x2="300" y2="90" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
                                        <line x1="0" y1="135" x2="300" y2="135" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />

                                        {/* Gradient fill */}
                                        <defs>
                                            <linearGradient id="trendGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                                <stop offset="0%" stopColor="rgba(100,100,100,0.3)" />
                                                <stop offset="100%" stopColor="rgba(100,100,100,0.0)" />
                                            </linearGradient>
                                        </defs>

                                        {/* Area under curve */}
                                        <path
                                            d="M0,140 L30,120 L60,130 L90,110 L120,115 L150,100 L180,105 L210,90 L240,95 L270,80 L300,85 L300,180 L0,180 Z"
                                            fill="url(#trendGradient)"
                                        />

                                        {/* Trend line */}
                                        <path
                                            d="M0,140 L30,120 L60,130 L90,110 L120,115 L150,100 L180,105 L210,90 L240,95 L270,80 L300,85"
                                            fill="none"
                                            stroke="rgba(150,150,150,0.8)"
                                            strokeWidth="2"
                                        />
                                    </svg>

                                    <div className="absolute bottom-0 left-0 right-0 flex justify-between text-[8px] text-white/30 font-mono px-1">
                                        <span>8/11</span>
                                        <span>6/11</span>
                                    </div>
                                </div>
                            </div>

                            {/* Brands / Categories */}
                            <div className="rounded-lg border border-white/[0.08] bg-[#0f0f0f] p-6 hover:border-white/[0.15] transition-all duration-300">
                                <div className="flex items-center gap-2 mb-6">
                                    <svg width="12" height="12" viewBox="0 0 12 12" className="text-white/60">
                                        <circle cx="6" cy="6" r="5" stroke="currentColor" fill="none" strokeWidth="1" />
                                        <circle cx="6" cy="6" r="2" fill="currentColor" />
                                    </svg>
                                    <span className="text-[10px] uppercase tracking-[0.15em] text-white/60 font-medium">Risk Factors</span>
                                </div>

                                <div className="space-y-5">
                                    {metrics.factors.map((factor, i) => (
                                        <div key={i} className="flex items-center justify-between group hover:bg-white/[0.02] p-2 -mx-2 rounded transition-colors">
                                            <div className="flex items-center gap-3">
                                                <svg width="16" height="16" viewBox="0 0 16 16" className="text-white/40">
                                                    {i === 0 && <path d="M8 2L10 6H14L11 9L12 13L8 10L4 13L5 9L2 6H6L8 2Z" fill="currentColor" />}
                                                    {i === 1 && <path d="M3 8h10M8 3v10" stroke="currentColor" strokeWidth="1.5" fill="none" />}
                                                    {i === 2 && <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" />}
                                                    {i === 3 && <circle cx="8" cy="8" r="5" stroke="currentColor" strokeWidth="1.5" fill="none" />}
                                                    {i === 4 && <path d="M2 8l4 4 8-8" stroke="currentColor" strokeWidth="1.5" fill="none" />}
                                                    {i === 5 && <path d="M8 2v12M2 8h12" stroke="currentColor" strokeWidth="1.5" />}
                                                </svg>
                                                <span className="text-sm text-white/80">{factor.name}</span>
                                            </div>
                                            <span className="text-sm font-mono text-white/60">{factor.value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Location Dot Matrix */}
                            <div className="rounded-lg border border-white/[0.08] bg-[#0f0f0f] p-6 hover:border-white/[0.15] transition-all duration-300">
                                <div className="flex items-center gap-2 mb-6">
                                    <svg width="12" height="12" viewBox="0 0 12 12" className="text-white/60">
                                        <path d="M6 2L10 6L6 10L2 6Z" fill="currentColor" />
                                    </svg>
                                    <span className="text-[10px] uppercase tracking-[0.15em] text-white/60 font-medium">Location</span>
                                </div>

                                <div className="flex items-center justify-center h-48">
                                    <svg width="200" height="180" viewBox="0 0 200 180">
                                        {/* Generate dot matrix pattern */}
                                        {Array.from({ length: 20 }).map((_, row) =>
                                            Array.from({ length: 25 }).map((_, col) => {
                                                const isHotspot = (row > 8 && row < 14 && col > 12 && col < 18);
                                                const opacity = isHotspot ? 0.8 : Math.random() * 0.3;
                                                const color = isHotspot ? '#d4af37' : '#666666';
                                                return (
                                                    <circle
                                                        key={`${row}-${col}`}
                                                        cx={col * 8}
                                                        cy={row * 9}
                                                        r="1"
                                                        fill={color}
                                                        opacity={opacity}
                                                    />
                                                );
                                            })
                                        )}
                                    </svg>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Panel - Component Styles / Controls */}
                <div className="w-96 border-l border-white/[0.08] bg-[#0f0f0f] p-6 overflow-y-auto">
                    <h2 className="text-2xl font-light uppercase tracking-[0.3em] text-white/90 mb-8">
                        Component<br />Styles
                    </h2>

                    {/* Icon Grid */}
                    <div className="grid grid-cols-5 gap-4 mb-8">
                        {[
                            <path key="1" d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />,
                            <circle key="2" cx="12" cy="12" r="10" />,
                            <path key="3" d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />,
                            <path key="4" d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />,
                            <path key="5" d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />,
                            <path key="6" d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />,
                            <circle key="7" cx="12" cy="12" r="3" />,
                            <path key="8" d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />,
                            <path key="9" d="M12 2L2 7l10 5 10-5-10-5z" />,
                            <circle key="10" cx="12" cy="12" r="1" />
                        ].map((icon, i) => (
                            <button
                                key={i}
                                className="flex items-center justify-center h-10 rounded border border-white/10 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/20 transition-all"
                            >
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-white/50">
                                    {icon}
                                </svg>
                            </button>
                        ))}
                    </div>

                    {/* Search Input */}
                    <div className="mb-6">
                        <div className="flex items-center gap-2 px-4 py-3 rounded border border-white/10 bg-white/[0.02] focus-within:border-white/20 transition-colors">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white/40">
                                <circle cx="11" cy="11" r="8" />
                                <path d="m21 21-4.35-4.35" />
                            </svg>
                            <input
                                type="text"
                                placeholder="FIELD / PARCEL ID"
                                className="flex-1 bg-transparent text-xs text-white/60 placeholder:text-white/30 outline-none uppercase tracking-wider"
                            />
                        </div>
                    </div>

                    {/* Filters */}
                    <div className="space-y-4 mb-8">
                        {['All Crop Types', 'All Regions', 'All Risk Levels', 'Coverage Status'].map((label, i) => (
                            <div key={i} className="flex items-center justify-between px-4 py-3 rounded border border-white/10 bg-white/[0.02] hover:border-white/15 transition-colors cursor-pointer">
                                <span className="text-xs text-white/60 uppercase tracking-wider">{label}</span>
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white/40">
                                    <path d="m6 9 6 6 6-6" />
                                </svg>
                            </div>
                        ))}
                    </div>

                    {/* Top Risk Items */}
                    {metrics && (
                        <div className="space-y-4">
                            {metrics.factors.slice(0, 2).map((factor, i) => (
                                <div key={i} className="rounded-lg border border-white/[0.08] bg-[#141414] p-4 hover:border-[#d4af37]/30 transition-all">
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="text-xs text-[#d4af37] font-mono">No.{i + 1}</div>
                                        <div className="text-[10px] text-white/40 uppercase tracking-wider">{factor.impact}</div>
                                    </div>
                                    <div className="text-sm text-white/90 mb-2 font-medium">{factor.name}</div>
                                    <div className="text-xs text-white/50 mb-3">Impact Value: {factor.value}</div>

                                    {/* Mini bar chart */}
                                    <div className="flex items-end gap-[2px] h-8">
                                        {Array.from({ length: 12 }).map((_, idx) => (
                                            <div
                                                key={idx}
                                                className="flex-1 bg-[#d4af37]/20"
                                                style={{ height: `${Math.random() * 100}%` }}
                                            />
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Stats Summary */}
                    {metrics && (
                        <div className="mt-8 pt-6 border-t border-white/[0.08]">
                            <div className="grid grid-cols-2 gap-4 mb-4">
                                <div className="rounded border border-white/[0.08] bg-white/[0.02] p-4">
                                    <div className="text-[10px] text-white/40 uppercase tracking-wider mb-2">Premium</div>
                                    <div className="text-xl font-bold text-white">KES {metrics.premium.toLocaleString()}</div>
                                </div>
                                <div className="rounded border border-white/[0.08] bg-white/[0.02] p-4">
                                    <div className="text-[10px] text-white/40 uppercase tracking-wider mb-2">Coverage</div>
                                    <div className="text-xl font-bold text-white">KES {(metrics.max_coverage / 1000000).toFixed(1)}M</div>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="rounded border border-white/[0.08] bg-white/[0.02] p-4">
                                    <div className="text-[10px] text-white/40 uppercase tracking-wider mb-2">Deductible</div>
                                    <div className="text-lg font-bold text-white">KES {metrics.deductible.toLocaleString()}</div>
                                </div>
                                <div className="rounded border border-white/[0.08] bg-white/[0.02] p-4">
                                    <div className="text-[10px] text-white/40 uppercase tracking-wider mb-2">Period</div>
                                    <div className="text-sm font-medium text-white/80">{metrics.coverage_period || '12 months'}</div>
                                </div>
                            </div>
                            {metrics.recommended_actions && metrics.recommended_actions.length > 0 && (
                                <div className="mt-4 rounded border border-[#d4af37]/20 bg-[#d4af37]/5 p-4">
                                    <div className="text-[10px] text-[#d4af37] uppercase tracking-wider mb-3">Recommended Actions</div>
                                    <ul className="space-y-2">
                                        {metrics.recommended_actions.map((action, i) => (
                                            <li key={i} className="flex items-start gap-2 text-xs text-white/70">
                                                <span className="text-[#d4af37] mt-0.5">•</span>
                                                <span>{action}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
