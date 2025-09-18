/**
 * Settings Page - Cartrita AI OS v2
 *
 * User preferences and application configuration
 */

'use client';

import React, { useState } from 'react';
import { useAtom } from 'jotai';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { FadeInUp } from '@/components/ui/FadeInUp';
import { userAtom, userPreferencesAtom } from '@/lib/store/atoms';
import { useUser, useUpdateUserPreferences } from '@/lib/hooks/queries';
import { cn } from '@/lib/utils';
import {
  UserIcon,
  PaletteIcon,
  BellIcon,
  ShieldIcon,
  DatabaseIcon,
  KeyIcon,
  CheckIcon,
  SaveIcon
} from 'lucide-react';

const settingSections = [
  {
    id: 'profile',
    title: 'Profile',
    icon: UserIcon,
    description: 'Personal information and account details',
  },
  {
    id: 'appearance',
    title: 'Appearance',
    icon: PaletteIcon,
    description: 'Theme, colors, and display preferences',
  },
  {
    id: 'notifications',
    title: 'Notifications',
    icon: BellIcon,
    description: 'Alert preferences and communication settings',
  },
  {
    id: 'privacy',
    title: 'Privacy & Security',
    icon: ShieldIcon,
    description: 'Data protection and security settings',
  },
  {
    id: 'data',
    title: 'Data Management',
    icon: DatabaseIcon,
    description: 'Export, import, and manage your data',
  },
  {
    id: 'api',
    title: 'API Keys',
    icon: KeyIcon,
    description: 'Configure AI model providers and API access',
  },
];

export default function SettingsPage() {
  const [user] = useAtom(userAtom);
  const [preferences, setPreferences] = useAtom(userPreferencesAtom);
  const [activeSection, setActiveSection] = useState('profile');
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  // Query hooks
  const { data: serverUser, isLoading } = useUser();
  const { mutate: updatePreferences, isPending: isUpdating } = useUpdateUserPreferences();

  const displayUser = serverUser || user;

  const handlePreferenceChange = (key: string, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value,
    }));
    setUnsavedChanges(true);
  };

  const handleSaveChanges = () => {
    updatePreferences(preferences, {
      onSuccess: () => {
        setUnsavedChanges(false);
      },
    });
  };

  const renderProfileSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-100 mb-4">
          Profile Information
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Full Name
            </label>
            <input
              type="text"
              value={displayUser?.name || ''}
              disabled
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={displayUser?.email || ''}
              disabled
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 disabled:opacity-50"
            />
          </div>
        </div>

        <p className="text-xs text-gray-500 mt-2">
          Profile information is managed through your account provider.
        </p>
      </div>
    </div>
  );

  const renderAppearanceSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-100 mb-4">
          Theme & Display
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Theme
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => handlePreferenceChange('theme', 'dark')}
                className={cn(
                  'p-4 border rounded-lg transition-colors text-left',
                  preferences.theme === 'dark'
                    ? 'border-copilot-blue bg-copilot-blue/10'
                    : 'border-gray-700 bg-gray-800 hover:bg-gray-700'
                )}
              >
                <div className="flex items-center gap-3">
                  <div className="w-4 h-4 bg-gray-900 rounded border border-gray-600" />
                  <span className="text-sm font-medium text-gray-200">Dark</span>
                  {preferences.theme === 'dark' && (
                    <CheckIcon className="w-4 h-4 text-copilot-blue ml-auto" />
                  )}
                </div>
              </button>

              <button
                onClick={() => handlePreferenceChange('theme', 'light')}
                className={cn(
                  'p-4 border rounded-lg transition-colors text-left opacity-50 cursor-not-allowed',
                  'border-gray-700 bg-gray-800'
                )}
                disabled
              >
                <div className="flex items-center gap-3">
                  <div className="w-4 h-4 bg-gray-100 rounded border border-gray-300" />
                  <span className="text-sm font-medium text-gray-200">Light</span>
                  <span className="text-xs text-gray-500 ml-auto">Coming Soon</span>
                </div>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Language
            </label>
            <select
              value={preferences.language}
              onChange={(e) => handlePreferenceChange('language', e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:border-copilot-blue/50"
            >
              <option value="en">English</option>
              <option value="es">Español (Coming Soon)</option>
              <option value="fr">Français (Coming Soon)</option>
              <option value="de">Deutsch (Coming Soon)</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );

  const renderNotificationsSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-100 mb-4">
          Notification Preferences
        </h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-200">
                Desktop Notifications
              </p>
              <p className="text-xs text-gray-400">
                Get notified when agents complete tasks
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.notifications}
                onChange={(e) => handlePreferenceChange('notifications', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-copilot-blue"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-200">
                Auto-save Conversations
              </p>
              <p className="text-xs text-gray-400">
                Automatically save chat history
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.autoSave}
                onChange={(e) => handlePreferenceChange('autoSave', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-copilot-blue"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSection = () => {
    switch (activeSection) {
      case 'profile':
        return renderProfileSection();
      case 'appearance':
        return renderAppearanceSection();
      case 'notifications':
        return renderNotificationsSection();
      default:
        return (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <p className="text-gray-400">
                This section is coming soon.
              </p>
            </div>
          </div>
        );
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading settings..." />
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="flex-1 flex flex-col h-full bg-gray-950">
        {/* Header */}
        <div className="flex-shrink-0 px-6 py-6 border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-100 mb-2">
                Settings
              </h1>
              <p className="text-gray-400">
                Manage your preferences and account settings
              </p>
            </div>

            {unsavedChanges && (
              <button
                onClick={handleSaveChanges}
                disabled={isUpdating}
                className="flex items-center gap-2 px-4 py-2 bg-copilot-blue hover:bg-copilot-blue/80 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                <SaveIcon className="w-4 h-4" />
                {isUpdating ? 'Saving...' : 'Save Changes'}
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar */}
          <div className="w-64 border-r border-gray-800 bg-gray-900/30">
            <nav className="p-4 space-y-1">
              {settingSections.map((section) => {
                const Icon = section.icon;
                return (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left transition-colors',
                      activeSection === section.id
                        ? 'bg-copilot-blue/10 text-copilot-blue border border-copilot-blue/30'
                        : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                    )}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium">
                        {section.title}
                      </p>
                      <p className="text-xs opacity-70 truncate">
                        {section.description}
                      </p>
                    </div>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-6">
              <FadeInUp key={activeSection}>
                {renderSection()}
              </FadeInUp>
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
