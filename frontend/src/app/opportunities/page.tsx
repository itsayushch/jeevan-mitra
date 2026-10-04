"use client";
import { useEffect, useState } from 'react';
import { opportunitiesApi } from '../../lib/api/opportunities';
import { OpportunitySubmissionForm } from '../../components/modules/OpportunitySubmissionForm';

export default function Page() {
    const [opportunities, setOpportunities] = useState<any[]>([]);
    const [qualifications, setQualifications] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const opps = await opportunitiesApi.listOpportunities();
            setOpportunities(opps);
            const quals = await opportunitiesApi.listQualifications();
            setQualifications(quals);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    if (loading) return <div className="p-8">Loading opportunities...</div>;

    return (
        <div className="max-w-4xl mx-auto p-6 space-y-8">
            <div>
                <h1 className="text-3xl font-bold mb-2">My Opportunities</h1>
                <p className="text-gray-600">Explore local training and job opportunities based on your skills.</p>
            </div>

            {/* Multimodal Opportunity Submission Form */}
            <div className="my-6">
                <OpportunitySubmissionForm onSubmitted={fetchData} />
            </div>

            <div className="space-y-4">
                <h2 className="text-xl font-bold">Verified Matches (Local Availability)</h2>
                {opportunities.length === 0 ? (
                    <p className="text-gray-500">No verified local opportunities available right now.</p>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {opportunities.map(opp => (
                            <div key={opp.id} className="border p-4 rounded-lg border-green-500 bg-green-50 shadow-sm relative">
                                <span className="absolute top-2 right-2 bg-green-200 text-green-800 text-xs px-2 py-1 rounded-full font-bold">VERIFIED</span>
                                <h3 className="font-semibold text-lg">{opp.title}</h3>
                                <p className="text-sm text-gray-700 mt-1">{opp.summary}</p>
                                <div className="mt-4 text-sm text-gray-600 flex flex-col gap-1">
                                    <span>📍 {opp.district_id} {opp.location_text ? `- ${opp.location_text}` : ''}</span>
                                    <span>🪑 {opp.seats_available} Seats Available</span>
                                    <span>📅 Delivery: {opp.delivery_mode.replace('_', ' ')}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="space-y-4 mt-8">
                <h2 className="text-xl font-bold">Interest Matches (Qualifications)</h2>
                <p className="text-sm text-gray-500">These courses match your interests but may not have confirmed local batches right now.</p>
                {qualifications.length === 0 ? (
                    <p className="text-gray-500">No interest matches found.</p>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {qualifications.map(qual => (
                            <div key={qual.id} className="border p-4 rounded-lg bg-white shadow-sm opacity-80 hover:opacity-100 transition-opacity">
                                <span className="text-xs text-blue-600 font-bold uppercase tracking-wider mb-2 block">INTEREST MATCH</span>
                                <h3 className="font-semibold text-lg">{qual.title}</h3>
                                <p className="text-sm text-gray-700 mt-1 line-clamp-2">{qual.description}</p>
                                <div className="mt-4 text-sm text-gray-500 flex gap-4">
                                    <span>Sector: {qual.sector}</span>
                                    {qual.duration_hours && <span>⏱️ {qual.duration_hours} hrs</span>}
                                </div>
                                <button className="mt-4 text-blue-600 text-sm font-medium hover:underline">
                                    Notify me when local batch opens
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
