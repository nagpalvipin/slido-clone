/**
 * Main App Component
 * 
 * Root application component with routing and layout structure.
 * Handles navigation between host dashboard, attendee interface, and auth flows.
 */

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useParams, useNavigate } from 'react-router-dom';
import { HostDashboard } from './components/HostDashboard';
import { AttendeeInterface } from './components/AttendeeInterface';
import { api, CreateEventRequest } from './services/api';

// Home page component
const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md mx-auto text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Slido Clone</h1>
        <p className="text-gray-600 mb-8">
          Interactive Q&A and Live Polling for Events
        </p>
        
        <div className="space-y-4">
          <div className="p-6 bg-white rounded-lg shadow border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Join an Event</h2>
            <p className="text-sm text-gray-600 mb-4">
              Enter the event code to participate in polls and Q&A
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                const eventCode = formData.get('eventCode') as string;
                if (eventCode) {
                  window.location.href = `/events/${eventCode.toLowerCase()}`;
                }
              }}
            >
              <div className="flex space-x-2">
                <input
                  type="text"
                  name="eventCode"
                  placeholder="Event code"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Join
                </button>
              </div>
            </form>
          </div>
          
          <div className="p-6 bg-white rounded-lg shadow border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Host an Event</h2>
            <p className="text-sm text-gray-600 mb-4">
              Create and manage your own interactive event
            </p>
            <button
              onClick={() => {
                window.location.href = '/host/create';
              }}
              className="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              Create Event
            </button>
          </div>
        </div>
        
        <div className="mt-8 text-xs text-gray-500">
          <p>Built with React, TypeScript, and Tailwind CSS</p>
        </div>
      </div>
    </div>
  );
};

// Host Authentication Component
const HostAuth: React.FC = () => {
  const [hostCode, setHostCode] = useState('');
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { eventSlug } = useParams<{ eventSlug: string }>();
  const navigate = useNavigate();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!hostCode.trim()) {
      setError('Host code is required');
      return;
    }

    try {
      setIsAuthenticating(true);
      setError(null);

      // Store host code and attempt to access host view
      localStorage.setItem('hostCode', hostCode);
      api.auth.setHostCode(hostCode);

      // Verify access by trying to get host view
      await api.events.getHostView(eventSlug || '', hostCode);
      
      // Success - redirect to host dashboard
      navigate(`/host/${eventSlug}`);
    } catch (err) {
      setError('Invalid host code. Please check and try again.');
      localStorage.removeItem('hostCode');
    } finally {
      setIsAuthenticating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md mx-auto">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Host Authentication
          </h1>
          
          <p className="text-gray-600 mb-6 text-center">
            Enter your host code to access the event management dashboard.
          </p>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          <form onSubmit={handleAuth}>
            <div className="mb-4">
              <label htmlFor="hostCode" className="block text-sm font-medium text-gray-700 mb-2">
                Host Code
              </label>
              <input
                type="password"
                id="hostCode"
                value={hostCode}
                onChange={(e) => setHostCode(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter host code"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isAuthenticating}
              className="w-full px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
            >
              {isAuthenticating ? 'Authenticating...' : 'Access Dashboard'}
            </button>
          </form>
          
          <div className="mt-4 text-center">
            <button
              onClick={() => navigate(`/events/${eventSlug}`)}
              className="text-sm text-indigo-600 hover:text-indigo-500"
            >
              Join as attendee instead
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Event Creation Component
const EventCreation: React.FC = () => {
  const [formData, setFormData] = useState({
    title: '',
    slug: '',
    description: '',
    hostCode: ''
  });
  const [useCustomHostCode, setUseCustomHostCode] = useState(false);
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  // Generate slug from title
  const generateSlug = (title: string) => {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
      .replace(/\s+/g, '-') // Replace spaces with hyphens
      .replace(/-+/g, '-') // Replace multiple hyphens with single
      .replace(/^-|-$/g, '') // Remove leading/trailing hyphens
      .slice(0, 50); // Limit to 50 characters
  };

  // Handle title change and auto-generate slug
  const handleTitleChange = (title: string) => {
    setFormData(prev => ({
      ...prev,
      title,
      slug: prev.slug === generateSlug(prev.title) ? generateSlug(title) : prev.slug
    }));
  };

  // Validate custom host code format (simplified)
  const validateHostCode = (code: string): boolean => {
    // Must be 3-30 characters: alphanumeric, hyphens, underscores
    // Backend will auto-prefix with 'host_' if not present
    const cleaned = code.trim();
    if (!cleaned) return false;
    
    // Remove 'host_' prefix if present for validation
    const codeToValidate = cleaned.toLowerCase().startsWith('host_') 
      ? cleaned.slice(5) 
      : cleaned;
    
    // Check: 3-30 chars, alphanumeric + hyphens + underscores
    return /^[a-z0-9_-]{3,30}$/i.test(codeToValidate);
  };

  // Validation functions
  const validateForm = () => {
    const newErrors: {[key: string]: string} = {};

    // Title validation (1-200 characters)
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (formData.title.length < 1 || formData.title.length > 200) {
      newErrors.title = 'Title must be between 1 and 200 characters';
    }

    // Slug validation (3-50 characters, alphanumeric and hyphens only)
    if (!formData.slug.trim()) {
      newErrors.slug = 'Event code is required';
    } else if (formData.slug.length < 3 || formData.slug.length > 50) {
      newErrors.slug = 'Event code must be between 3 and 50 characters';
    } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      newErrors.slug = 'Event code can only contain lowercase letters, numbers, and hyphens';
    }

    // Host code validation (if custom code is enabled)
    if (useCustomHostCode) {
      const trimmedHostCode = formData.hostCode.trim();
      if (!trimmedHostCode) {
        newErrors.hostCode = 'Host code is required when using custom code';
      } else if (!validateHostCode(trimmedHostCode)) {
        newErrors.hostCode = 'Host code must be 3-30 characters (letters, numbers, hyphens, underscores only)';
      }
    }

    // Description validation (max 1000 characters, optional)
    if (formData.description && formData.description.length > 1000) {
      newErrors.description = 'Description must be 1000 characters or less';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      setIsSubmitting(true);
      setErrors({});

      const eventData = {
        title: formData.title.trim(),
        slug: formData.slug.trim(),
        description: formData.description.trim() || undefined
      };

      // Add custom host code if enabled (backend will sanitize and prefix)
      const eventDataWithCode: CreateEventRequest = useCustomHostCode && formData.hostCode.trim()
        ? { ...eventData, host_code: formData.hostCode.trim() }
        : eventData;

      const createdEvent = await api.events.create(eventDataWithCode);
      
      // Store the host code for automatic authentication
      localStorage.setItem('hostCode', createdEvent.host_code);
      api.auth.setHostCode(createdEvent.host_code);
      
      // Redirect to host dashboard
      navigate(`/host/${createdEvent.slug}`);
    } catch (err: any) {
      if (err.status === 409) {
        // Check if error is about host_code or slug
        const errorMessage = err.response?.detail || '';
        if (errorMessage.toLowerCase().includes('host_code') || errorMessage.toLowerCase().includes('host code')) {
          setErrors({ hostCode: 'This host code is already in use. Please choose a different one.' });
        } else {
          setErrors({ slug: 'Event code already exists. Please choose a different one.' });
        }
      } else if (err.status === 422) {
        const errorMessage = err.response?.detail || '';
        if (errorMessage.toLowerCase().includes('host_code') || errorMessage.toLowerCase().includes('host code')) {
          setErrors({ hostCode: 'Invalid host code format. Must be host_[a-z0-9]{12} (e.g., host_abc123def456)' });
        } else {
          setErrors({ general: 'Invalid input. Please check your entries and try again.' });
        }
      } else {
        setErrors({ general: 'Failed to create event. Please try again.' });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-lg w-full mx-auto">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Create New Event</h1>
            <p className="text-gray-600 mt-2">
              Set up your interactive Q&A and polling session
            </p>
          </div>

          {errors.general && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Title Field */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                Event Title *
              </label>
              <input
                type="text"
                id="title"
                value={formData.title}
                onChange={(e) => handleTitleChange(e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                  errors.title ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : 'border-gray-300 focus:border-indigo-500'
                }`}
                placeholder="Enter your event title"
                maxLength={200}
                required
              />
              {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title}</p>}
              <p className="mt-1 text-xs text-gray-500">{formData.title.length}/200 characters</p>
            </div>

            {/* Slug Field */}
            <div>
              <label htmlFor="slug" className="block text-sm font-medium text-gray-700 mb-1">
                Event Code *
              </label>
              <input
                type="text"
                id="slug"
                value={formData.slug}
                onChange={(e) => setFormData(prev => ({ ...prev, slug: e.target.value.toLowerCase() }))}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                  errors.slug ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : 'border-gray-300 focus:border-indigo-500'
                }`}
                placeholder="event-code-123"
                maxLength={50}
                required
              />
              {errors.slug && <p className="mt-1 text-sm text-red-600">{errors.slug}</p>}
              <p className="mt-1 text-xs text-gray-500">
                Attendees will use this code to join. Only lowercase letters, numbers, and hyphens allowed.
              </p>
            </div>

            {/* Description Field */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                Description (Optional)
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                  errors.description ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : 'border-gray-300 focus:border-indigo-500'
                }`}
                placeholder="Describe your event (optional)"
                rows={3}
                maxLength={1000}
              />
              {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description}</p>}
              <p className="mt-1 text-xs text-gray-500">{formData.description.length}/1000 characters</p>
            </div>

            {/* Custom Host Code Section */}
            <div className="border-t border-gray-200 pt-4">
              <div className="flex items-center mb-3">
                <input
                  type="checkbox"
                  id="useCustomHostCode"
                  checked={useCustomHostCode}
                  onChange={(e) => {
                    setUseCustomHostCode(e.target.checked);
                    if (!e.target.checked) {
                      setFormData(prev => ({ ...prev, hostCode: '' }));
                      setErrors(prev => {
                        const newErrors = { ...prev };
                        delete newErrors.hostCode;
                        return newErrors;
                      });
                    }
                  }}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="useCustomHostCode" className="ml-2 block text-sm font-medium text-gray-700">
                  Use custom host code
                </label>
              </div>
              
              {useCustomHostCode && (
                <div>
                  <label htmlFor="hostCode" className="block text-sm font-medium text-gray-700 mb-1">
                    Custom Host Code *
                  </label>
                  <input
                    type="text"
                    id="hostCode"
                    value={formData.hostCode}
                    onChange={(e) => setFormData(prev => ({ ...prev, hostCode: e.target.value }))}
                    onBlur={() => {
                      // Validate on blur
                      if (formData.hostCode.trim() && !validateHostCode(formData.hostCode.trim())) {
                        setErrors(prev => ({ 
                          ...prev, 
                          hostCode: 'Host code must be 3-30 characters (letters, numbers, hyphens, underscores only)' 
                        }));
                      } else {
                        setErrors(prev => {
                          const newErrors = { ...prev };
                          delete newErrors.hostCode;
                          return newErrors;
                        });
                      }
                    }}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                      errors.hostCode ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : 'border-gray-300 focus:border-indigo-500'
                    }`}
                    placeholder="myteam2025"
                    maxLength={35}
                    required={useCustomHostCode}
                  />
                  {errors.hostCode && <p className="mt-1 text-sm text-red-600">{errors.hostCode}</p>}
                  <p className="mt-1 text-xs text-gray-500">
                    Enter 3-30 characters (letters, numbers, hyphens, underscores). Backend will auto-prefix with "host_".
                    {formData.hostCode && ` (${formData.hostCode.length} chars)`}
                  </p>
                </div>
              )}
              
              {!useCustomHostCode && (
                <p className="text-xs text-gray-500 italic">
                  A secure host code will be automatically generated for you.
                </p>
              )}
            </div>

            {/* Feature Info */}
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Your event will support:</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Anonymous or named attendee participation</li>
                <li>• Live polling with real-time results (5-10 polls per session)</li>
                <li>• Q&A with automatic approval and upvoting</li>
                <li>• Support for 50-200 concurrent attendees</li>
                <li>• Permanent data retention for future reference</li>
              </ul>
            </div>

            {/* Actions */}
            <div className="flex space-x-4">
              <button
                type="button"
                onClick={() => navigate('/')}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
              >
                {isSubmitting ? 'Creating...' : 'Create Event'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Main App Component
export const App: React.FC = () => {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Home page */}
          <Route path="/" element={<HomePage />} />
          
          {/* Attendee routes */}
          <Route path="/events/:eventSlug" element={<AttendeeInterface />} />
          
          {/* Host routes */}
          <Route path="/host/create" element={<EventCreation />} />
          <Route path="/host/:eventSlug/auth" element={<HostAuth />} />
          <Route path="/host/:eventSlug" element={<HostDashboard />} />
          
          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;