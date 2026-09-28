/**
 * Calculate geographical distance in kilometers between two GPS coordinates
 * using the Haversine formula.
 */
export function calculateDistanceKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // Earth's radius in kilometers
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c;
  return Math.round(distance * 10) / 10;
}

/**
 * Standard block coordinates for pilot district Moradabad & adjacent Sambhal
 */
export const BLOCK_COORDINATES: Record<string, { lat: number; lon: number }> = {
  'Moradabad Rural': { lat: 28.8386, lon: 78.7733 },
  'Chhajlet': { lat: 28.9856, lon: 78.6811 },
  'Bahjoi': { lat: 28.4000, lon: 78.6300 }, // ~45 km away, used in solution proposal supply-gap cluster alert
  'Bilari': { lat: 28.6256, lon: 78.8022 },
  'Kundarki': { lat: 28.7056, lon: 78.7844 },
  'Bhagatpur Tanda': { lat: 28.9950, lon: 78.9400 },
  'Munda Pandey': { lat: 28.7800, lon: 78.9500 },
  'District Centre / Industrial Area': { lat: 28.8350, lon: 78.7700 }
};

export function getBlockCoordinates(blockName: string): { lat: number; lon: number } {
  return BLOCK_COORDINATES[blockName] || { lat: 28.8386, lon: 78.7733 };
}
