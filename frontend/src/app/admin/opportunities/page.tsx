"use client";
import { useEffect, useState } from 'react';
import { opportunitiesApi } from '../../../lib/api/opportunities';

export default function AdminOpportunitiesPage() {
    const [qualifications, setQualifications] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                const quals = await opportunitiesApi.listQualifications();
                setQualifications(quals);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    const handleCreateOpportunity = async (qualId: string) => {
        // Example integration
        const providerData = {
            provider_type: 'training_centre',
            name: 'New Training Centre',
            district_id: 'Moradabad',
            status: 'ACTIVE'
        };
        // Ideally we'd have a provider selection. Mocking for UI demonstration:
        alert("This would open a modal to select a provider and create an opportunity for qualification: " + qualId);
    };

    if (loading) return <div className="p-8">Loading...</div>;

    return (
        <div className="max-w-6xl mx-auto p-6 space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold mb-2">Staff Opportunity Management</h1>
                    <p className="text-gray-600">Verify and manage local opportunities against approved qualifications.</p>
                </div>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Approved Qualifications</h2>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead>
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sector</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {qualifications.map((qual) => (
                                <tr key={qual.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">{qual.title}</div>
                                        <div className="text-sm text-gray-500">{qual.id}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {qual.sector}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                            {qual.verification_status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button 
                                            onClick={() => handleCreateOpportunity(qual.id)}
                                            className="text-blue-600 hover:text-blue-900"
                                        >
                                            Add Local Opportunity
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
