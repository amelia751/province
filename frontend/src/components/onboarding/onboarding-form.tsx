"use client";

import { useState } from "react";
import moment from "moment-timezone";
import Select from "react-select";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";

// Import US regions and cities data
const usRegions = require('us-regions');
const { usaStatesFull, usaCities } = require('typed-usa-states');

// Define types for region and jurisdiction options
interface RegionOption {
  value: string;
  label: string;
  stateCode: string | null;
  stateName: string;
  region: string;
}

interface RegionGroup {
  label: string;
  options: RegionOption[];
}

interface JurisdictionOption {
  value: string;
  label: string;
  type: 'city' | 'county' | 'federal_district' | 'major_city';
  state: string;
  stateCode: string;
}

interface JurisdictionGroup {
  label: string;
  options: JurisdictionOption[];
}

const PRACTICE_AREAS = [
  "ADA Title II (Public Entities)",
  "ADA Title III (Public Accommodations)",
  "Product Liability",
  "Healthcare Law",
  "Employment Law",
  "Civil Rights",
  "Consumer Protection",
  "Regulatory Compliance"
];



/**
 * Generate region options using us-regions package
 * 
 * This creates a hierarchical structure with:
 * - Northeast Region (9 states)
 * - Midwest Region (13 states) 
 * - South Region (17 states)
 * - West Region (13 states)
 * - US Territories & Military (5 territories + military codes)
 * - Multi-Jurisdictional (special categories)
 * 
 * Each state/territory shows full name with abbreviation, e.g., "California (CA)"
 */
const generateRegionOptions = (): RegionGroup[] => {
  const states: { [key: string]: string } = usRegions.US_STATES_AND_TERRITORIES;
  const regions: { [key: string]: string[] } = usRegions.US_REGIONS;

  // Create grouped options by region
  const groupedOptions: RegionGroup[] = [];

  // Add US regions as groups
  Object.keys(regions).forEach(regionName => {
    const regionStates = regions[regionName]
      .filter((stateCode: string) => states[stateCode]) // Only include states that exist in our data
      .map((stateCode: string): RegionOption => ({
        value: stateCode,
        label: `${states[stateCode]} (${stateCode})`,
        stateCode,
        stateName: states[stateCode],
        region: regionName
      }))
      .sort((a: RegionOption, b: RegionOption) => a.stateName.localeCompare(b.stateName));

    if (regionStates.length > 0) {
      groupedOptions.push({
        label: `${regionName} Region`,
        options: regionStates
      });
    }
  });

  // Add territories as a separate group
  const territories = ['AS', 'GU', 'MP', 'PR', 'VI', 'AA', 'AE', 'AP']
    .filter(code => states[code])
    .map((code: string): RegionOption => ({
      value: code,
      label: `${states[code]} (${code})`,
      stateCode: code,
      stateName: states[code],
      region: 'Territories'
    }))
    .sort((a: RegionOption, b: RegionOption) => a.stateName.localeCompare(b.stateName));

  if (territories.length > 0) {
    groupedOptions.push({
      label: 'US Territories & Military',
      options: territories
    });
  }

  // Add special categories
  groupedOptions.push({
    label: 'Multi-Jurisdictional',
    options: [
      { value: 'multi-regional', label: 'Multi-Regional (US)', stateCode: null, stateName: 'Multi-Regional (US)', region: 'Special' },
      { value: 'national', label: 'National (US)', stateCode: null, stateName: 'National (US)', region: 'Special' },
      { value: 'international', label: 'International', stateCode: null, stateName: 'International', region: 'Special' },
      { value: 'other', label: 'Other', stateCode: null, stateName: 'Other', region: 'Special' }
    ]
  });

  return groupedOptions;
};

const REGION_OPTIONS = generateRegionOptions();

/**
 * Generate jurisdiction options (cities, counties, federal districts) for a given state
 */
const generateJurisdictionOptions = (stateCode: string): JurisdictionGroup[] => {
  if (!stateCode || stateCode.length !== 2) return [];

  const state = usaStatesFull.find((s: any) => s.abbreviation === stateCode);
  if (!state) return [];

  const jurisdictionGroups: JurisdictionGroup[] = [];

  // Major cities for the state
  const stateCities = usaCities
    .filter((city: any) => city.state === state.name)
    .slice(0, 30) // Limit to top 30 cities to avoid overwhelming the dropdown
    .map((city: any): JurisdictionOption => ({
      value: `${city.name}, ${stateCode}`,
      label: city.name,
      type: 'city' as const,
      state: state.name,
      stateCode: stateCode
    }))
    .sort((a: JurisdictionOption, b: JurisdictionOption) => a.label.localeCompare(b.label));

  if (stateCities.length > 0) {
    jurisdictionGroups.push({
      label: 'Major Cities',
      options: stateCities
    });
  }

  // Counties for the state
  const stateCounties = state.counties
    .map((county: string): JurisdictionOption => ({
      value: `${county}, ${stateCode}`,
      label: county,
      type: 'county' as const,
      state: state.name,
      stateCode: stateCode
    }))
    .sort((a: JurisdictionOption, b: JurisdictionOption) => a.label.localeCompare(b.label));

  if (stateCounties.length > 0) {
    jurisdictionGroups.push({
      label: 'Counties',
      options: stateCounties
    });
  }

  // Federal district courts (major ones)
  const federalDistricts = getFederalDistrictsForState(stateCode);
  if (federalDistricts.length > 0) {
    jurisdictionGroups.push({
      label: 'Federal Districts',
      options: federalDistricts
    });
  }

  return jurisdictionGroups;
};

/**
 * Get federal district courts for a state (simplified mapping)
 */
const getFederalDistrictsForState = (stateCode: string): JurisdictionOption[] => {
  const federalDistrictMap: { [key: string]: string[] } = {
    'CA': ['N.D. Cal.', 'C.D. Cal.', 'S.D. Cal.', 'E.D. Cal.'],
    'NY': ['S.D.N.Y.', 'E.D.N.Y.', 'N.D.N.Y.', 'W.D.N.Y.'],
    'TX': ['N.D. Tex.', 'S.D. Tex.', 'E.D. Tex.', 'W.D. Tex.'],
    'FL': ['S.D. Fla.', 'M.D. Fla.', 'N.D. Fla.'],
    'IL': ['N.D. Ill.', 'C.D. Ill.', 'S.D. Ill.'],
    'PA': ['E.D. Pa.', 'M.D. Pa.', 'W.D. Pa.'],
    'OH': ['N.D. Ohio', 'S.D. Ohio'],
    'GA': ['N.D. Ga.', 'M.D. Ga.', 'S.D. Ga.'],
    'NC': ['E.D.N.C.', 'M.D.N.C.', 'W.D.N.C.'],
    'VA': ['E.D. Va.', 'W.D. Va.'],
    'WA': ['W.D. Wash.', 'E.D. Wash.'],
    'MA': ['D. Mass.'],
    'MD': ['D. Md.'],
    'DC': ['D.D.C.'],
    'CO': ['D. Colo.'],
    'MI': ['E.D. Mich.', 'W.D. Mich.'],
    'NJ': ['D.N.J.'],
    'CT': ['D. Conn.'],
    'OR': ['D. Or.'],
    'AZ': ['D. Ariz.'],
    'NV': ['D. Nev.'],
    'UT': ['D. Utah'],
    'WI': ['E.D. Wis.', 'W.D. Wis.'],
    'MN': ['D. Minn.'],
    'LA': ['E.D. La.', 'M.D. La.', 'W.D. La.'],
    'AL': ['N.D. Ala.', 'M.D. Ala.', 'S.D. Ala.'],
    'SC': ['D.S.C.'],
    'TN': ['E.D. Tenn.', 'M.D. Tenn.', 'W.D. Tenn.'],
    'KY': ['E.D. Ky.', 'W.D. Ky.'],
    'MO': ['E.D. Mo.', 'W.D. Mo.'],
    'KS': ['D. Kan.'],
    'IA': ['N.D. Iowa', 'S.D. Iowa'],
    'AR': ['E.D. Ark.', 'W.D. Ark.'],
    'MS': ['N.D. Miss.', 'S.D. Miss.'],
    'OK': ['N.D. Okla.', 'E.D. Okla.', 'W.D. Okla.'],
    'IN': ['N.D. Ind.', 'S.D. Ind.'],
    'WV': ['N.D.W.Va.', 'S.D.W.Va.'],
  };

  const districts = federalDistrictMap[stateCode] || [];
  const stateName = usaStatesFull.find((s: any) => s.abbreviation === stateCode)?.name || stateCode;

  return districts.map(district => ({
    value: `${district}`,
    label: district,
    type: 'federal_district' as const,
    state: stateName,
    stateCode: stateCode
  }));
};

/**
 * Generate timezone options based on US regions
 * Prioritizes common US timezones and includes others
 */
const generateTimezoneOptions = () => {
  const commonUSTimezones = [
    'America/New_York',      // Eastern
    'America/Chicago',       // Central  
    'America/Denver',        // Mountain
    'America/Los_Angeles',   // Pacific
    'America/Anchorage',     // Alaska
    'Pacific/Honolulu',      // Hawaii
  ];

  const allTimezones = moment.tz.names()
    .filter(tz => tz.startsWith('America/') || tz.startsWith('Pacific/'))
    .filter(tz => !commonUSTimezones.includes(tz))
    .sort();

  return [
    ...commonUSTimezones.map(tz => ({
      value: tz,
      label: `${moment.tz(tz).format('z')} - ${tz.split('/')[1].replace('_', ' ')}`,
      isCommon: true
    })),
    ...allTimezones.map(tz => ({
      value: tz,
      label: `${moment.tz(tz).format('z')} - ${tz.split('/')[1].replace('_', ' ')}`,
      isCommon: false
    }))
  ];
};

/**
 * Get default timezone based on state/region
 */
const getDefaultTimezone = (stateCode: string): string => {
  const timezoneMap: { [key: string]: string } = {
    // Eastern Time
    'CT': 'America/New_York', 'DE': 'America/New_York', 'FL': 'America/New_York',
    'GA': 'America/New_York', 'ME': 'America/New_York', 'MD': 'America/New_York',
    'MA': 'America/New_York', 'NH': 'America/New_York', 'NJ': 'America/New_York',
    'NY': 'America/New_York', 'NC': 'America/New_York', 'OH': 'America/New_York',
    'PA': 'America/New_York', 'RI': 'America/New_York', 'SC': 'America/New_York',
    'VT': 'America/New_York', 'VA': 'America/New_York', 'WV': 'America/New_York',
    'DC': 'America/New_York',

    // Central Time
    'AL': 'America/Chicago', 'AR': 'America/Chicago', 'IL': 'America/Chicago',
    'IA': 'America/Chicago', 'KS': 'America/Chicago', 'KY': 'America/Chicago',
    'LA': 'America/Chicago', 'MN': 'America/Chicago', 'MS': 'America/Chicago',
    'MO': 'America/Chicago', 'NE': 'America/Chicago', 'ND': 'America/Chicago',
    'OK': 'America/Chicago', 'SD': 'America/Chicago', 'TN': 'America/Chicago',
    'TX': 'America/Chicago', 'WI': 'America/Chicago',

    // Mountain Time
    'AZ': 'America/Denver', 'CO': 'America/Denver', 'ID': 'America/Denver',
    'MT': 'America/Denver', 'NV': 'America/Denver', 'NM': 'America/Denver',
    'UT': 'America/Denver', 'WY': 'America/Denver',

    // Pacific Time
    'CA': 'America/Los_Angeles', 'OR': 'America/Los_Angeles', 'WA': 'America/Los_Angeles',

    // Alaska Time
    'AK': 'America/Anchorage',

    // Hawaii Time
    'HI': 'Pacific/Honolulu',
  };

  return timezoneMap[stateCode] || 'America/Chicago'; // Default to Central
};

const TIMEZONE_OPTIONS = generateTimezoneOptions();

// Helper function to format time labels
const formatTimeLabel = (hour: number): string => {
  if (hour === 0) return "12:00 AM";
  if (hour < 12) return `${hour}:00 AM`;
  if (hour === 12) return "12:00 PM";
  return `${hour - 12}:00 PM`;
};

// Custom shadcn-like theme for react-select
const customSelectStyles = {
  control: (provided: any, state: any) => ({
    ...provided,
    backgroundColor: 'white',
    borderColor: state.isFocused ? '#000000' : '#e2e8f0',
    borderWidth: '1px',
    borderRadius: '6px',
    boxShadow: state.isFocused ? '0 0 0 2px rgba(0, 0, 0, 0.1)' : 'none',
    minHeight: '40px',
    fontSize: '14px',
    '&:hover': {
      borderColor: state.isFocused ? '#000000' : '#cbd5e1',
    },
  }),
  valueContainer: (provided: any) => ({
    ...provided,
    padding: '2px 12px',
  }),
  input: (provided: any) => ({
    ...provided,
    margin: '0px',
    color: '#0f172a',
  }),
  indicatorSeparator: () => ({
    display: 'none',
  }),
  indicatorsContainer: (provided: any) => ({
    ...provided,
    paddingRight: '8px',
  }),
  dropdownIndicator: (provided: any, state: any) => ({
    ...provided,
    color: state.isFocused ? '#000000' : '#64748b',
    padding: '4px',
    '&:hover': {
      color: '#000000',
    },
  }),
  placeholder: (provided: any) => ({
    ...provided,
    color: '#94a3b8',
    fontSize: '14px',
  }),
  singleValue: (provided: any) => ({
    ...provided,
    color: '#0f172a',
    fontSize: '14px',
  }),
  menu: (provided: any) => ({
    ...provided,
    backgroundColor: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    zIndex: 9999,
  }),
  menuList: (provided: any) => ({
    ...provided,
    padding: '4px',
    maxHeight: '200px',
  }),
  option: (provided: any, state: any) => ({
    ...provided,
    backgroundColor: state.isSelected
      ? '#000000'
      : state.isFocused
        ? '#f1f5f9'
        : 'white',
    color: state.isSelected ? 'white' : '#0f172a',
    padding: '8px 12px',
    fontSize: '14px',
    borderRadius: '4px',
    margin: '1px 0',
    cursor: 'pointer',
    '&:hover': {
      backgroundColor: state.isSelected ? '#000000' : '#f1f5f9',
    },
  }),
  group: (provided: any) => ({
    ...provided,
    paddingTop: '0',
    paddingBottom: '0',
  }),
  groupHeading: (provided: any) => ({
    ...provided,
    backgroundColor: '#f8fafc',
    color: '#374151',
    fontSize: '12px',
    fontWeight: '600',
    padding: '8px 12px 4px 12px',
    margin: '4px 0 2px 0',
    borderRadius: '4px',
    textTransform: 'none',
  }),
  multiValue: (provided: any) => ({
    ...provided,
    backgroundColor: '#f1f5f9',
    borderRadius: '4px',
    border: '1px solid #e2e8f0',
  }),
  multiValueLabel: (provided: any) => ({
    ...provided,
    color: '#0f172a',
    fontSize: '12px',
    padding: '2px 6px',
  }),
  multiValueRemove: (provided: any) => ({
    ...provided,
    color: '#64748b',
    borderRadius: '0 4px 4px 0',
    '&:hover': {
      backgroundColor: '#ef4444',
      color: 'white',
    },
  }),
};

interface OnboardingFormProps {
  onComplete: (data: any) => Promise<void>;
  loading: boolean;
}

export default function OnboardingForm({ onComplete, loading }: OnboardingFormProps) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: "",
    region: "",
    specific_jurisdictions: [] as string[], // Cities, counties, federal districts
    website: "",
    timezone: "America/Chicago",
    practice_areas: [] as string[],
    jurisdictions: [] as string[],
    digest_cadence: "weekly" as "daily" | "weekly",
    digest_hour_local: 9,
    keywords_include: [] as string[],
    keywords_exclude: [] as string[],
  });

  // Generate dynamic jurisdictions based on selected region
  const getDynamicJurisdictions = (stateCode: string): string[] => {
    const baseJurisdictions = [
      "Federal (All Districts)"
    ];

    if (stateCode === 'MO') {
      return [
        "Missouri (MO)",
        "W.D. Missouri",
        "E.D. Missouri",
        "8th Circuit",
        ...baseJurisdictions
      ];
    } else if (stateCode === 'KS') {
      return [
        "Kansas (KS)",
        "D. Kansas",
        "10th Circuit",
        ...baseJurisdictions
      ];
    } else if (stateCode && stateCode.length === 2) {
      const stateName = usaStatesFull.find((s: any) => s.abbreviation === stateCode)?.name;
      const federalDistricts = getFederalDistrictsForState(stateCode);

      return [
        `${stateName} (${stateCode})`,
        ...federalDistricts.map(d => d.label),
        ...baseJurisdictions
      ];
    }

    return [
      "Missouri (MO)",
      "Kansas (KS)",
      "W.D. Missouri",
      "D. Kansas",
      "8th Circuit",
      "10th Circuit",
      ...baseJurisdictions
    ];
  };


  const handleNext = () => {
    if (step < 4) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleArrayToggle = (field: 'practice_areas' | 'jurisdictions', value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(item => item !== value)
        : [...prev[field], value]
    }));
  };

  const handleKeywordAdd = (field: 'keywords_include' | 'keywords_exclude', value: string) => {
    if (value.trim() && !formData[field].includes(value.trim())) {
      setFormData(prev => ({
        ...prev,
        [field]: [...prev[field], value.trim()]
      }));
    }
  };

  const handleKeywordRemove = (field: 'keywords_include' | 'keywords_exclude', value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter(item => item !== value)
    }));
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return formData.name.trim().length > 0;
      case 2:
        return formData.practice_areas.length > 0 && formData.jurisdictions.length > 0;
      case 3:
        return true; // Alert preferences are optional
      case 4:
        return true; // Keywords are optional
      default:
        return false;
    }
  };

  const handleSubmit = async () => {
    await onComplete(formData);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center mb-4">
            <div className="w-8 h-8 bg-white rounded-md"></div>
          </div>
          <CardTitle className="text-2xl font-bold">Welcome to Province</CardTitle>
          <CardDescription>
            Let's set up your organization - Step {step} of 4
          </CardDescription>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(step / 4) * 100}%` }}
            ></div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Organization Details</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Organization Name *
                  </label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter your organization name"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Primary State/Region
                  </label>
                  <Select<RegionOption>
                    options={REGION_OPTIONS}
                    value={REGION_OPTIONS.flatMap(group => group.options).find(r => r.value === formData.region) || null}
                    onChange={(selectedOption) => {
                      const newRegion = (selectedOption as RegionOption)?.value || "";
                      setFormData(prev => ({
                        ...prev,
                        region: newRegion,
                        timezone: getDefaultTimezone(newRegion), // Auto-set timezone based on state
                        specific_jurisdictions: [], // Reset jurisdictions when region changes
                        jurisdictions: [] // Reset selected jurisdictions
                      }));
                    }}
                    placeholder="Select your primary state/region..."
                    isSearchable
                    styles={customSelectStyles}
                    formatGroupLabel={(data) => data.label}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Website <span className="text-gray-500 font-normal">(Optional)</span>
                  </label>
                  <Input
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData(prev => ({ ...prev, website: e.target.value }))}
                    placeholder="https://example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Timezone
                  </label>
                  <Select
                    options={[
                      {
                        label: 'Common US Timezones',
                        options: TIMEZONE_OPTIONS.filter(tz => tz.isCommon)
                      },
                      {
                        label: 'Other Timezones',
                        options: TIMEZONE_OPTIONS.filter(tz => !tz.isCommon)
                      }
                    ]}
                    value={TIMEZONE_OPTIONS.find(tz => tz.value === formData.timezone) || null}
                    onChange={(selectedOption: any) => {
                      setFormData(prev => ({ ...prev, timezone: selectedOption?.value || 'America/Chicago' }));
                    }}
                    placeholder="Select timezone..."
                    isSearchable
                    styles={customSelectStyles}
                    formatGroupLabel={(data) => data.label}
                  />
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Practice Areas *</h3>
                <div className="grid grid-cols-2 gap-2">
                  {PRACTICE_AREAS.map(area => (
                    <label key={area} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.practice_areas.includes(area)}
                        onChange={() => handleArrayToggle('practice_areas', area)}
                        className="rounded"
                      />
                      <span className="text-sm">{area}</span>
                    </label>
                  ))}
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="text-lg font-semibold mb-4">
                  Jurisdictions *
                  {formData.region && (
                    <span className="text-sm font-normal text-gray-600 ml-2">
                      (Based on {REGION_OPTIONS.flatMap(g => g.options).find(r => r.value === formData.region)?.stateName || formData.region})
                    </span>
                  )}
                </h3>
                <div className="grid grid-cols-1 gap-2">
                  {getDynamicJurisdictions(formData.region).map(jurisdiction => (
                    <label key={jurisdiction} className="flex items-center space-x-2 cursor-pointer p-2 rounded hover:bg-gray-50">
                      <input
                        type="checkbox"
                        checked={formData.jurisdictions.includes(jurisdiction)}
                        onChange={() => handleArrayToggle('jurisdictions', jurisdiction)}
                        className="rounded"
                      />
                      <span className="text-sm">{jurisdiction}</span>
                    </label>
                  ))}
                </div>
                {!formData.region && (
                  <p className="text-sm text-gray-500 mt-2">
                    Select a state/region above to see relevant jurisdictions
                  </p>
                )}
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold">Alert Preferences</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Digest Frequency
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        value="weekly"
                        checked={formData.digest_cadence === "weekly"}
                        onChange={(e) => setFormData(prev => ({ ...prev, digest_cadence: e.target.value as "weekly" }))}
                      />
                      <span>Weekly (Recommended)</span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        value="daily"
                        checked={formData.digest_cadence === "daily"}
                        onChange={(e) => setFormData(prev => ({ ...prev, digest_cadence: e.target.value as "daily" }))}
                      />
                      <span>Daily</span>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Preferred Time (Local)
                  </label>
                  <Select
                    options={[
                      {
                        label: 'Morning',
                        options: Array.from({ length: 6 }, (_, i) => i + 6).map(hour => ({
                          value: hour,
                          label: hour === 12 ? "12:00 PM" : `${hour}:00 AM`
                        }))
                      },
                      {
                        label: 'Afternoon',
                        options: Array.from({ length: 6 }, (_, i) => i + 12).map(hour => ({
                          value: hour,
                          label: hour === 12 ? "12:00 PM" : `${hour - 12}:00 PM`
                        }))
                      },
                      {
                        label: 'Evening',
                        options: Array.from({ length: 6 }, (_, i) => i + 18).map(hour => ({
                          value: hour,
                          label: `${hour - 12}:00 PM`
                        }))
                      },
                      {
                        label: 'Late Night',
                        options: Array.from({ length: 6 }, (_, i) => i).map(hour => ({
                          value: hour,
                          label: hour === 0 ? "12:00 AM" : `${hour}:00 AM`
                        }))
                      }
                    ]}
                    value={{ value: formData.digest_hour_local, label: formatTimeLabel(formData.digest_hour_local) }}
                    onChange={(selectedOption: any) => {
                      setFormData(prev => ({ ...prev, digest_hour_local: selectedOption?.value || 9 }));
                    }}
                    placeholder="Select preferred time..."
                    styles={customSelectStyles}
                    formatGroupLabel={(data) => data.label}
                  />
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold">Keywords (Optional)</h3>
              <p className="text-sm text-gray-600">
                Add keywords to refine your alerts. We'll include sensible defaults for your practice areas.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Include Keywords (alerts will prioritize these)
                  </label>
                  <KeywordInput
                    keywords={formData.keywords_include}
                    onAdd={(value) => handleKeywordAdd('keywords_include', value)}
                    onRemove={(value) => handleKeywordRemove('keywords_include', value)}
                    placeholder="Add keyword to include..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Exclude Keywords (alerts will avoid these)
                  </label>
                  <KeywordInput
                    keywords={formData.keywords_exclude}
                    onAdd={(value) => handleKeywordAdd('keywords_exclude', value)}
                    onRemove={(value) => handleKeywordRemove('keywords_exclude', value)}
                    placeholder="Add keyword to exclude..."
                  />
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-between pt-6">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={step === 1}
            >
              Back
            </Button>

            {step < 4 ? (
              <Button
                onClick={handleNext}
                disabled={!canProceed()}
              >
                Next
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={loading}
              >
                {loading ? "Setting up..." : "Complete Setup"}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function KeywordInput({
  keywords,
  onAdd,
  onRemove,
  placeholder
}: {
  keywords: string[];
  onAdd: (value: string) => void;
  onRemove: (value: string) => void;
  placeholder: string;
}) {
  const [input, setInput] = useState("");

  const handleAdd = () => {
    if (input.trim()) {
      onAdd(input);
      setInput("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
        />
        <Button type="button" onClick={handleAdd} size="sm">
          Add
        </Button>
      </div>
      {keywords.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {keywords.map(keyword => (
            <span
              key={keyword}
              className="inline-flex items-center px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full"
            >
              {keyword}
              <button
                onClick={() => onRemove(keyword)}
                className="ml-1 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}