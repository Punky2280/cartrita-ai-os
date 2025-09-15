// Cartrita AI OS - Settings Panel Component
// Comprehensive user settings with preferences, API keys, and configuration

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  Settings,
  User,
  Key,
  Palette,
  Bell,
  Shield,
  Database,
  Download,
  Upload,
  Trash2,
  Eye,
  EyeOff,
  Save,
  AlertTriangle,
  Info,
  X,
} from "lucide-react";
import { cn } from "@/utils";
import {
  Input,
  Label,
  Textarea,
  Switch,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Alert,
  AlertDescription,
} from "@/components/ui";
import { useSettings, useUpdateSettings } from "@/hooks";
import type {
  User as UserType,
  UserSettings,
  Theme,
  PrivacySettings,
} from "@/types";

// API Key Input Component
function ApiKeyInput({
  label,
  value,
  onChange,
  placeholder,
  description,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  description?: string;
  required?: boolean;
}) {
  const [showKey, setShowKey] = useState(false);

  return (
    <div className="space-y-2">
      <Label htmlFor={label.toLowerCase().replace(/\s+/g, "-")}>
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      <div className="relative">
        <Input
          id={label.toLowerCase().replace(/\s+/g, "-")}
          type={showKey ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="pr-10"
        />
        <button
          type="button"
          onClick={() => setShowKey(!showKey)}
          className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0 hover:bg-accent hover:text-accent-foreground rounded-md"
        >
          {showKey ? (
            <EyeOff className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
        </button>
      </div>
      {description && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}
    </div>
  );
}

// Profile Settings Tab
function ProfileSettings({
  settings,
  onUpdate,
}: {
  settings: UserSettings;
  onUpdate: (updates: Partial<UserSettings>) => void;
}) {
  const [formData, setFormData] = useState({
    name: settings.name || "",
    email: settings.email || "",
    bio: settings.bio || "",
    avatar: settings.avatar || "",
  });

  const handleSave = useCallback(() => {
    onUpdate(formData);
    toast.success("Profile updated successfully");
  }, [formData, onUpdate]);

  const handleChange = useCallback((field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Profile Information</h3>
        <p className="text-sm text-muted-foreground">
          Update your personal information and profile settings.
        </p>
      </div>

      <div className="grid gap-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="name">Full Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => handleChange("name", e.target.value)}
              placeholder="Enter your full name"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleChange("email", e.target.value)}
              placeholder="Enter your email"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="avatar">Avatar URL</Label>
          <Input
            id="avatar"
            value={formData.avatar}
            onChange={(e) => handleChange("avatar", e.target.value)}
            placeholder="https://example.com/avatar.jpg"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="bio">Bio</Label>
          <Textarea
            id="bio"
            value={formData.bio}
            onChange={(e) => handleChange("bio", e.target.value)}
            placeholder="Tell us about yourself..."
            rows={3}
          />
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
        >
          <Save className="h-4 w-4 mr-2" />
          Save Changes
        </button>
      </div>
    </div>
  );
}

// API Keys Settings Tab
function ApiKeysSettings({
  settings,
  onUpdate,
}: {
  settings: UserSettings;
  onUpdate: (updates: Partial<UserSettings>) => void;
}) {
  const [apiKeys, setApiKeys] = useState({
    openai: settings.apiKeys?.openai || "",
    google: settings.apiKeys?.google || "",
    huggingface: settings.apiKeys?.huggingface || "",
  });

  const handleSave = useCallback(() => {
    onUpdate({ apiKeys });
    toast.success("API keys updated successfully");
  }, [apiKeys, onUpdate]);

  const handleKeyChange = useCallback((provider: string, value: string) => {
    setApiKeys((prev) => ({ ...prev, [provider]: value }));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">API Keys</h3>
        <p className="text-sm text-muted-foreground">
          Configure your API keys for different AI providers. Keys are encrypted
          and stored securely.
        </p>
      </div>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Your API keys are encrypted at rest and never exposed in logs or
          responses. Make sure to keep them secure and rotate them regularly.
        </AlertDescription>
      </Alert>

      <div className="space-y-4">
        <ApiKeyInput
          label="OpenAI API Key"
          value={apiKeys.openai}
          onChange={(value) => handleKeyChange("openai", value)}
          placeholder="sk-..."
          description="Required for GPT models and DALL-E image generation"
        />

        <ApiKeyInput
          label="Google AI API Key"
          value={apiKeys.google}
          onChange={(value) => handleKeyChange("google", value)}
          placeholder="AIza..."
          description="Required for Gemini models and Google services"
        />

        <ApiKeyInput
          label="Hugging Face API Key"
          value={apiKeys.huggingface}
          onChange={(value) => handleKeyChange("huggingface", value)}
          placeholder="hf_..."
          description="Required for Hugging Face models and datasets"
        />
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
        >
          <Save className="h-4 w-4 mr-2" />
          Save API Keys
        </button>
      </div>
    </div>
  );
}

// Appearance Settings Tab
function AppearanceSettings({
  settings,
  onUpdate,
}: {
  settings: UserSettings;
  onUpdate: (updates: Partial<UserSettings>) => void;
}) {
  const handleThemeChange = useCallback(
    (value: string) => {
      onUpdate({ theme: value as Theme });
      toast.success("Theme updated successfully");
    },
    [onUpdate],
  );

  const handleSettingChange = useCallback(
    (key: string, value: unknown) => {
      onUpdate({
        appearance: {
          ...settings.appearance,
          [key]: value,
        },
      });
    },
    [settings.appearance, onUpdate],
  );

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Appearance</h3>
        <p className="text-sm text-muted-foreground">
          Customize the look and feel of your Cartrita AI OS experience.
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Theme</Label>
          <Select value={settings.theme} onValueChange={handleThemeChange}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="light">Light</SelectItem>
              <SelectItem value="dark">Dark</SelectItem>
              <SelectItem value="system">System</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Compact Mode</Label>
              <p className="text-sm text-muted-foreground">
                Use smaller spacing and components
              </p>
            </div>
            <Switch
              checked={settings.appearance?.compactMode || false}
              onCheckedChange={(checked) =>
                handleSettingChange("compactMode", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Show Animations</Label>
              <p className="text-sm text-muted-foreground">
                Enable smooth transitions and animations
              </p>
            </div>
            <Switch
              checked={settings.appearance?.showAnimations ?? true}
              onCheckedChange={(checked) =>
                handleSettingChange("showAnimations", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>High Contrast</Label>
              <p className="text-sm text-muted-foreground">
                Increase contrast for better accessibility
              </p>
            </div>
            <Switch
              checked={settings.appearance?.highContrast || false}
              onCheckedChange={(checked) =>
                handleSettingChange("highContrast", checked)
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// Notifications Settings Tab
function NotificationsSettings({
  settings,
  onUpdate,
}: {
  settings: UserSettings;
  onUpdate: (updates: Partial<UserSettings>) => void;
}) {
  const handleNotificationChange = useCallback(
    (key: string, value: unknown) => {
      onUpdate({
        notifications: {
          ...settings.notifications,
          [key]: value,
        },
      });
    },
    [settings.notifications, onUpdate],
  );

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Notifications</h3>
        <p className="text-sm text-muted-foreground">
          Configure how and when you receive notifications.
        </p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Email Notifications</Label>
            <p className="text-sm text-muted-foreground">
              Receive notifications via email
            </p>
          </div>
          <Switch
            checked={settings.notifications?.email || false}
            onCheckedChange={(checked) =>
              handleNotificationChange("email", checked)
            }
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Push Notifications</Label>
            <p className="text-sm text-muted-foreground">
              Receive push notifications in your browser
            </p>
          </div>
          <Switch
            checked={settings.notifications?.push || false}
            onCheckedChange={(checked) =>
              handleNotificationChange("push", checked)
            }
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Message Notifications</Label>
            <p className="text-sm text-muted-foreground">
              Get notified about new messages and responses
            </p>
          </div>
          <Switch
            checked={settings.notifications?.messages ?? true}
            onCheckedChange={(checked) =>
              handleNotificationChange("messages", checked)
            }
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Agent Status Notifications</Label>
            <p className="text-sm text-muted-foreground">
              Get notified when agents go online/offline
            </p>
          </div>
          <Switch
            checked={settings.notifications?.agentStatus || false}
            onCheckedChange={(checked) =>
              handleNotificationChange("agentStatus", checked)
            }
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>System Updates</Label>
            <p className="text-sm text-muted-foreground">
              Receive notifications about system updates and maintenance
            </p>
          </div>
          <Switch
            checked={settings.notifications?.systemUpdates || false}
            onCheckedChange={(checked) =>
              handleNotificationChange("systemUpdates", checked)
            }
          />
        </div>
      </div>
    </div>
  );
}

// Privacy Settings Tab
function PrivacySettings({
  settings,
  onUpdate,
}: {
  settings: UserSettings;
  onUpdate: (updates: Partial<UserSettings>) => void;
}) {
  const handlePrivacyChange = useCallback(
    (key: string, value: unknown) => {
      onUpdate({
        privacy: {
          ...settings.privacy,
          [key]: value,
        },
      });
    },
    [settings.privacy, onUpdate],
  );

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Privacy & Security</h3>
        <p className="text-sm text-muted-foreground">
          Control your privacy settings and data sharing preferences.
        </p>
      </div>

      <Alert>
        <Shield className="h-4 w-4" />
        <AlertDescription>
          Your conversations and data are encrypted and never shared with third
          parties without your consent.
        </AlertDescription>
      </Alert>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Data Collection</Label>
            <p className="text-sm text-muted-foreground">
              Allow anonymous usage analytics to improve the service
            </p>
          </div>
          <Switch
            checked={settings.privacy?.dataCollection ?? true}
            onCheckedChange={(checked) =>
              handlePrivacyChange("dataCollection", checked)
            }
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Conversation History</Label>
            <p className="text-sm text-muted-foreground">
              Save conversation history for future reference
            </p>
          </div>
          <Switch
            checked={settings.privacy?.saveHistory ?? true}
            onCheckedChange={(checked) =>
              handlePrivacyChange("saveHistory", checked)
            }
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Profile Visibility</Label>
            <p className="text-sm text-muted-foreground">
              Make your profile visible to other users
            </p>
          </div>
          <Switch
            checked={settings.privacy?.profileVisibility || false}
            onCheckedChange={(checked) =>
              handlePrivacyChange("profileVisibility", checked)
            }
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Activity Status</Label>
            <p className="text-sm text-muted-foreground">
              Show when you&apos;re online and active
            </p>
          </div>
          <Switch
            checked={settings.privacy?.showActivity ?? true}
            onCheckedChange={(checked) =>
              handlePrivacyChange("showActivity", checked)
            }
          />
        </div>
      </div>
    </div>
  );
}

// Data Management Tab
function DataManagement({
  onExport,
  onImport,
  onDelete,
}: {
  onExport: () => void;
  onImport: (file: File) => void;
  onDelete: () => void;
}) {
  const [confirmDelete, setConfirmDelete] = useState("");
  const [importFile, setImportFile] = useState<File | null>(null);

  const handleImport = useCallback(() => {
    if (importFile) {
      onImport(importFile);
      setImportFile(null);
    }
  }, [importFile, onImport]);

  const handleDelete = useCallback(() => {
    if (confirmDelete === "DELETE") {
      onDelete();
      setConfirmDelete("");
    }
  }, [confirmDelete, onDelete]);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Data Management</h3>
        <p className="text-sm text-muted-foreground">
          Export, import, or delete your data. These actions cannot be undone.
        </p>
      </div>

      <div className="space-y-4">
        {/* Export Data */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Download className="h-4 w-4" />
              Export Data
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Download all your conversations, settings, and data in JSON
              format.
            </p>
            <button
              onClick={onExport}
              className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
            >
              <Download className="h-4 w-4 mr-2" />
              Export Data
            </button>
          </CardContent>
        </Card>

        {/* Import Data */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Import Data
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Import data from a previously exported JSON file.
            </p>
            <div className="space-y-2">
              <Input
                type="file"
                accept=".json"
                onChange={(e) => setImportFile(e.target.files?.[0] || null)}
              />
              <button
                onClick={handleImport}
                disabled={!importFile}
                className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
              >
                <Upload className="h-4 w-4 mr-2" />
                Import Data
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Delete Data */}
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-destructive">
              <Trash2 className="h-4 w-4" />
              Delete All Data
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Permanently delete all your conversations, settings, and data.
              This action cannot be undone.
            </p>
            <Alert className="mb-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                This will permanently delete all your data. Type
                &quot;DELETE&quot; to confirm.
              </AlertDescription>
            </Alert>
            <div className="space-y-2">
              <Input
                value={confirmDelete}
                onChange={(e) => setConfirmDelete(e.target.value)}
                placeholder="Type DELETE to confirm"
              />
              <button
                onClick={handleDelete}
                disabled={confirmDelete !== "DELETE"}
                className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-destructive text-destructive-foreground hover:bg-destructive/90 h-10 px-4 py-2"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete All Data
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Main Settings Panel Component
interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

export function SettingsPanel({
  isOpen,
  onClose,
  className,
}: SettingsPanelProps) {
  const { data: settings, isLoading } = useSettings();
  const updateSettings = useUpdateSettings();

  const handleUpdateSettings = useCallback(
    async (updates: Partial<UserType["preferences"]>) => {
      try {
        await updateSettings.mutateAsync(updates);
      } catch (error) {
        toast.error("Failed to update settings");
      }
    },
    [updateSettings],
  );

  const handleExport = useCallback(() => {
    // Implement data export
    toast.success("Data export started");
  }, []);

  const handleImport = useCallback((file: File) => {
    // Implement data import
    toast.success("Data import started");
  }, []);

  const handleDelete = useCallback(() => {
    // Implement data deletion
    toast.success("Data deletion started");
  }, []);

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, x: "100%" }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: "100%" }}
        className={cn(
          "fixed right-0 top-0 h-full w-full max-w-2xl bg-background shadow-2xl overflow-hidden",
          className,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Settings
          </h2>
          <button
            onClick={onClose}
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-9 rounded-md px-3"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : settings ? (
            <Tabs defaultValue="profile" className="h-full flex flex-col">
              <TabsList className="grid w-full grid-cols-6 mx-6 mt-4">
                <TabsTrigger value="profile" className="text-xs">
                  <User className="h-4 w-4 mr-1" />
                  Profile
                </TabsTrigger>
                <TabsTrigger value="api-keys" className="text-xs">
                  <Key className="h-4 w-4 mr-1" />
                  API Keys
                </TabsTrigger>
                <TabsTrigger value="appearance" className="text-xs">
                  <Palette className="h-4 w-4 mr-1" />
                  Appearance
                </TabsTrigger>
                <TabsTrigger value="notifications" className="text-xs">
                  <Bell className="h-4 w-4 mr-1" />
                  Notifications
                </TabsTrigger>
                <TabsTrigger value="privacy" className="text-xs">
                  <Shield className="h-4 w-4 mr-1" />
                  Privacy
                </TabsTrigger>
                <TabsTrigger value="data" className="text-xs">
                  <Database className="h-4 w-4 mr-1" />
                  Data
                </TabsTrigger>
              </TabsList>

              <div className="flex-1 overflow-y-auto p-6">
                <TabsContent value="profile" className="mt-0">
                  <ProfileSettings
                    settings={settings}
                    onUpdate={handleUpdateSettings}
                  />
                </TabsContent>

                <TabsContent value="api-keys" className="mt-0">
                  <ApiKeysSettings
                    settings={settings}
                    onUpdate={handleUpdateSettings}
                  />
                </TabsContent>

                <TabsContent value="appearance" className="mt-0">
                  <AppearanceSettings
                    settings={settings}
                    onUpdate={handleUpdateSettings}
                  />
                </TabsContent>

                <TabsContent value="notifications" className="mt-0">
                  <NotificationsSettings
                    settings={settings}
                    onUpdate={handleUpdateSettings}
                  />
                </TabsContent>

                <TabsContent value="privacy" className="mt-0">
                  <PrivacySettings
                    settings={settings}
                    onUpdate={handleUpdateSettings}
                  />
                </TabsContent>

                <TabsContent value="data" className="mt-0">
                  <DataManagement
                    onExport={handleExport}
                    onImport={handleImport}
                    onDelete={handleDelete}
                  />
                </TabsContent>
              </div>
            </Tabs>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-muted-foreground">Failed to load settings</p>
                <button
                  onClick={() => window.location.reload()}
                  className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 rounded-md px-3 mt-4"
                >
                  Reload
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

// Compact settings button
export function SettingsButton({
  onClick,
  className,
}: {
  onClick: () => void;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-9 rounded-md px-3",
        className,
      )}
    >
      <Settings className="h-4 w-4" />
    </button>
  );
}
