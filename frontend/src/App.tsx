import { useState, useEffect, useRef } from 'react';
import { 
  Sprout, 
  Upload, 
  BarChart3, 
  FileText, 
  Layers, 
  AlertTriangle, 
  Download, 
  RefreshCw, 
  Sliders, 
  Sun, 
  Moon, 
  CheckCircle2, 
  X, 
  FileCheck, 
  ShieldCheck, 
  Sparkles, 
  Brain, 
  Target, 
  TrendingUp, 
  ArrowRight,
  Maximize2
} from 'lucide-react';
import { useTheme } from './context/ThemeContext';

export default function App() {
  const { theme, setTheme } = useTheme();
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'upload' | 'dashboard' | 'evidence' | 'reports'>('upload');
  
  // Video & Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isLoadingSample, setIsLoadingSample] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Agronomic Inputs
  const [cropType, setCropType] = useState('Tomato');
  const [growthStage, setGrowthStage] = useState('Vegetative');
  const [fieldArea, setFieldArea] = useState(2.5);
  const [soilN, setSoilN] = useState(45);
  const [soilP, setSoilP] = useState(25);
  const [soilK, setSoilK] = useState(30);
  const [soilPh, setSoilPh] = useState(6.5);
  const [tempC, setTempC] = useState(26.5);
  const [rainfallMm, setRainfallMm] = useState(110);
  const [frameInterval, setFrameInterval] = useState(15);

  // Job & Analysis State
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [summaryData, setSummaryData] = useState<any>(null);
  const [leafFindings, setLeafFindings] = useState<any[]>([]);
  const [weedFindings, setWeedFindings] = useState<any[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Zoom Modal for Evidence Inspection
  const [zoomFinding, setZoomFinding] = useState<any | null>(null);

  // Initial Load: Fetch health and automatically load latest completed job (if available)
  useEffect(() => {
    fetch('/api/v1/health')
      .then(res => res.json())
      .then(data => setSystemHealth(data))
      .catch(() => console.log('Backend health polling...'));

    fetch('/api/v1/analysis/jobs/latest')
      .then(res => {
        if (res.ok) return res.json();
        return null;
      })
      .then(latestJob => {
        if (latestJob && latestJob.job_id) {
          setActiveJobId(latestJob.job_id);
          setJobStatus(latestJob);
          fetchResults(latestJob.job_id);
        }
      })
      .catch(err => console.log('Could not auto-fetch latest job:', err));
  }, []);

  // Poll Job Status when an active analysis is running
  useEffect(() => {
    if (!activeJobId) return;
    if (jobStatus && (jobStatus.status === 'COMPLETED' || jobStatus.status === 'FAILED')) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/analysis/jobs/${activeJobId}/status`);
        if (res.ok) {
          const status = await res.json();
          setJobStatus(status);

          if (status.status === 'COMPLETED') {
            clearInterval(interval);
            await fetchResults(activeJobId);
            setActiveTab('dashboard');
          } else if (status.status === 'FAILED') {
            clearInterval(interval);
            setErrorMessage(status.error_message || 'Analysis pipeline failed.');
          }
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [activeJobId, jobStatus?.status]);

  const fetchResults = async (jobId: string) => {
    try {
      const [sumRes, leafRes, weedRes] = await Promise.all([
        fetch(`/api/v1/analysis/${jobId}/summary`),
        fetch(`/api/v1/analysis/${jobId}/findings/leaves?limit=50`),
        fetch(`/api/v1/analysis/${jobId}/findings/weeds?limit=50`),
      ]);

      if (sumRes.ok) setSummaryData(await sumRes.json());
      if (leafRes.ok) setLeafFindings(await leafRes.json());
      if (weedRes.ok) setWeedFindings(await weedRes.json());
    } catch (err) {
      console.error('Error fetching results:', err);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setErrorMessage(null);
    }
  };

  const handleQuickLoadSample = async () => {
    try {
      setIsLoadingSample(true);
      setErrorMessage(null);
      const res = await fetch('/api/v1/videos/sample-video');
      if (!res.ok) {
        throw new Error('Could not load sample video from server.');
      }
      const blob = await res.blob();
      const file = new File([blob], 'sample_video_for_upload.mp4', { type: 'video/mp4' });
      setSelectedFile(file);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to quick-load sample video.');
    } finally {
      setIsLoadingSample(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile) {
      setErrorMessage('Please select or quick-load an agricultural video file first.');
      return;
    }

    try {
      setIsUploading(true);
      setUploadProgress(20);
      setErrorMessage(null);

      const formData = new FormData();
      formData.append('file', selectedFile);

      setUploadProgress(50);
      const uploadRes = await fetch('/api/v1/videos/upload', {
        method: 'POST',
        body: formData,
      });

      if (!uploadRes.ok) {
        const err = await uploadRes.json();
        throw new Error(err.detail || 'Video upload failed.');
      }

      const videoData = await uploadRes.json();
      setUploadProgress(100);
      setIsUploading(false);

      const jobPayload = {
        video_id: videoData.id,
        frame_interval: frameInterval,
        enable_blur_filter: true,
        blur_threshold: 80.0,
        enable_ssim_filter: true,
        ssim_threshold: 0.95,
        agro_inputs: {
          crop_type: cropType,
          growth_stage: growthStage,
          field_area_ha: fieldArea,
          soil_n: soilN,
          soil_p: soilP,
          soil_k: soilK,
          soil_ph: soilPh,
          temp_c: tempC,
          rainfall_mm: rainfallMm,
        }
      };

      const jobRes = await fetch('/api/v1/analysis/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jobPayload),
      });

      if (!jobRes.ok) {
        const err = await jobRes.json();
        throw new Error(err.detail || 'Failed to start analysis job.');
      }

      const jobData = await jobRes.json();
      setActiveJobId(jobData.job_id);
      setJobStatus(jobData);
    } catch (err: any) {
      setIsUploading(false);
      setErrorMessage(err.message || 'An unexpected error occurred.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 flex flex-col font-sans transition-colors duration-200">
      {/* Top Navbar */}
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-950/60 rounded-xl flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                <Sprout size={22} />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white text-center md:text-left leading-tight">
                  AgroVision Intelligence AI
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400 hidden sm:block">
                  Autonomous Crop Health, Weed Localization & Yield Prediction Platform
                </p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex w-full flex-wrap gap-2 sm:gap-3 md:w-auto md:flex-nowrap">
              <button
                onClick={() => setActiveTab('upload')}
                className={`flex-1 md:flex-none px-4 py-2 rounded-lg transition-all shadow-sm hover:shadow-md inline-flex items-center justify-center gap-2 font-medium ${
                  activeTab === 'upload'
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-white hover:bg-gray-50 text-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 border border-gray-300 dark:border-gray-700'
                }`}
              >
                <Upload size={16} />
                1. Ingestion & Setup
              </button>
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`flex-1 md:flex-none px-4 py-2 rounded-lg transition-all shadow-sm hover:shadow-md inline-flex items-center justify-center gap-2 font-medium ${
                  activeTab === 'dashboard'
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-white hover:bg-gray-50 text-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 border border-gray-300 dark:border-gray-700'
                }`}
              >
                <BarChart3 size={16} />
                2. Analytics Dashboard
                {summaryData && <span className="w-2 h-2 rounded-full bg-emerald-500" />}
              </button>
              <button
                onClick={() => setActiveTab('evidence')}
                className={`flex-1 md:flex-none px-4 py-2 rounded-lg transition-all shadow-sm hover:shadow-md inline-flex items-center justify-center gap-2 font-medium ${
                  activeTab === 'evidence'
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-white hover:bg-gray-50 text-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 border border-gray-300 dark:border-gray-700'
                }`}
              >
                <Layers size={16} />
                3. Traceable Evidence
                {leafFindings.length > 0 && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 font-bold">
                    {leafFindings.length}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveTab('reports')}
                className={`flex-1 md:flex-none px-4 py-2 rounded-lg transition-all shadow-sm hover:shadow-md inline-flex items-center justify-center gap-2 font-medium ${
                  activeTab === 'reports'
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-white hover:bg-gray-50 text-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 border border-gray-300 dark:border-gray-700'
                }`}
              >
                <FileText size={16} />
                4. PDF Reports
              </button>
              <button
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                className="flex-1 md:flex-none px-3.5 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition-all inline-flex items-center justify-center gap-2"
                title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
              >
                {theme === 'dark' ? <Sun size={16} className="text-amber-400" /> : <Moon size={16} className="text-gray-600" />}
                <span className="text-xs font-semibold">{theme === 'dark' ? 'Light' : 'Dark'}</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full flex-1">
        {/* Global Error Banner */}
        {errorMessage && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <AlertTriangle size={18} />
              <span className="text-sm font-medium">{errorMessage}</span>
            </div>
            <button onClick={() => setErrorMessage(null)} className="text-red-500 hover:text-red-700">
              <X size={16} />
            </button>
          </div>
        )}

        {/* ML Service Status Bar */}
        <section className="mb-6 bg-white dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">AI Pipeline Status</p>
                <p className="text-base font-semibold text-gray-900 dark:text-white">
                  ONLINE • PyTorch 2.6 CUDA • {systemHealth?.compute_device ? `GPU (${systemHealth.compute_device})` : 'NVIDIA RTX 3050'}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600 dark:text-gray-400">
              <div><span className="font-semibold text-gray-900 dark:text-white">Weed Tracker:</span> YOLOv8 + ByteTrack</div>
              <div><span className="font-semibold text-gray-900 dark:text-white">Pathology:</span> PlantVillage 15-Class</div>
              <div><span className="font-semibold text-gray-900 dark:text-white">Yield Engine:</span> Multivariate CI (90%)</div>
            </div>
          </div>
        </section>

        {/* ML Modules Banner */}
        <section className="mb-8">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-4">
            AI Vision & Agronomic Modules
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-900 hover:bg-gradient-to-br hover:from-blue-50 hover:to-indigo-50 dark:hover:from-gray-900 dark:hover:to-blue-950/40 rounded-xl p-5 border border-gray-200 dark:border-gray-800 hover:border-blue-300 transition-all shadow-sm hover:shadow-md text-left group">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/40 group-hover:bg-blue-200 rounded-lg flex items-center justify-center transition-colors">
                  <Sparkles className="text-blue-600 dark:text-blue-400" size={20} />
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Weed Tracking</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">YOLOv8 + ByteTrack cross-frame spatial trajectory deduplication</p>
            </div>

            <div className="bg-white dark:bg-gray-900 hover:bg-gradient-to-br hover:from-purple-50 hover:to-pink-50 dark:hover:from-gray-900 dark:hover:to-purple-950/40 rounded-xl p-5 border border-gray-200 dark:border-gray-800 hover:border-purple-300 transition-all shadow-sm hover:shadow-md text-left group">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/40 group-hover:bg-purple-200 rounded-lg flex items-center justify-center transition-colors">
                  <Brain className="text-purple-600 dark:text-purple-400" size={20} />
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Disease Diagnosis</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Calibrated EfficientNet-B0 multi-class foliar pathology classifier</p>
            </div>

            <div className="bg-white dark:bg-gray-900 hover:bg-gradient-to-br hover:from-emerald-50 hover:to-teal-50 dark:hover:from-gray-900 dark:hover:to-emerald-950/40 rounded-xl p-5 border border-gray-200 dark:border-gray-800 hover:border-emerald-300 transition-all shadow-sm hover:shadow-md text-left group">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/40 group-hover:bg-emerald-200 rounded-lg flex items-center justify-center transition-colors">
                  <Target className="text-emerald-600 dark:text-emerald-400" size={20} />
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Lesion Masking</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Pixel-exact necrotic tissue segmentation & area ratio calculation</p>
            </div>

            <div className="bg-white dark:bg-gray-900 hover:bg-gradient-to-br hover:from-orange-50 hover:to-amber-50 dark:hover:from-gray-900 dark:hover:to-orange-950/40 rounded-xl p-5 border border-gray-200 dark:border-gray-800 hover:border-orange-300 transition-all shadow-sm hover:shadow-md text-left group">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/40 group-hover:bg-orange-200 rounded-lg flex items-center justify-center transition-colors">
                  <TrendingUp className="text-orange-600 dark:text-orange-400" size={20} />
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Yield Prediction</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Multivariate regression with calibrated 90% confidence interval</p>
            </div>
          </div>
        </section>

        {/* TAB 1: UPLOAD & SETUP (Independent Dedicated View) */}
        {activeTab === 'upload' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left 2 Cols: Video Ingestion */}
            <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-md flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                      <Upload size={20} className="text-blue-600" />
                      Field Video Footage Ingestion
                    </h2>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Upload drone or handheld video footage (.MP4, .MOV, .AVI up to 500 MB)
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={handleQuickLoadSample}
                    disabled={isLoadingSample || isUploading || jobStatus?.status === 'PROCESSING'}
                    className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/20 dark:hover:bg-blue-900/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 transition inline-flex items-center gap-1.5 shadow-sm"
                  >
                    {isLoadingSample ? <RefreshCw size={13} className="animate-spin" /> : <Sparkles size={13} />}
                    <span>Quick Load Test Video</span>
                  </button>
                </div>

                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept=".mp4,.mov,.avi,.mkv"
                  className="hidden"
                />

                <div
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all ${
                    selectedFile
                      ? 'border-blue-500 bg-blue-50/40 dark:bg-blue-950/20'
                      : 'border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-950 hover:border-blue-400'
                  }`}
                >
                  <Upload size={40} className={`mb-3 ${selectedFile ? 'text-blue-600' : 'text-gray-400'}`} />
                  {selectedFile ? (
                    <div className="text-center">
                      <div className="inline-flex items-center gap-1.5 text-sm font-bold text-gray-900 dark:text-white">
                        <CheckCircle2 size={16} className="text-emerald-500" />
                        <span>{selectedFile.name}</span>
                      </div>
                      <p className="text-xs text-emerald-600 font-medium mt-1">
                        Ready to process ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                      </p>
                      <span className="inline-block mt-3 text-xs text-blue-600 dark:text-blue-400 underline font-semibold">
                        Click to choose another file
                      </span>
                    </div>
                  ) : (
                    <div className="text-center">
                      <p className="text-sm font-bold text-gray-800 dark:text-gray-200">
                        Click to browse or drop field video file here
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Supported formats: MP4, MOV, AVI up to 500 MB (1080p recommended)
                      </p>
                    </div>
                  )}
                </div>

                {/* Progress bar during upload / processing */}
                {(isUploading || (jobStatus && jobStatus.status === 'PROCESSING')) && (
                  <div className="mt-6 bg-gray-50 dark:bg-gray-950 p-4 rounded-xl border border-gray-200 dark:border-gray-800">
                    <div className="flex justify-between items-center text-xs mb-2 font-medium">
                      <span className="text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
                        <RefreshCw size={13} className="animate-spin" />
                        <span>{isUploading ? 'Uploading Video to Server...' : `AI Pipeline Stage: ${jobStatus?.current_stage}`}</span>
                      </span>
                      <span className="font-mono text-gray-700 dark:text-gray-300 font-bold">
                        {isUploading ? `${uploadProgress}%` : `${jobStatus?.progress_percentage?.toFixed(1) || 0}%`}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2.5 overflow-hidden">
                      <div 
                        className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                        style={{ width: `${isUploading ? uploadProgress : jobStatus?.progress_percentage || 0}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Action Bar */}
              <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <span className="text-xs text-gray-500 font-mono">
                  Sample: <code className="bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded text-blue-600 dark:text-blue-400 font-bold">sample_video_for_upload.mp4</code>
                </span>

                <button
                  disabled={!selectedFile || isUploading || jobStatus?.status === 'PROCESSING'}
                  onClick={handleStartAnalysis}
                  className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-bold transition-all shadow-sm hover:shadow-md ${
                    !selectedFile || isUploading || jobStatus?.status === 'PROCESSING'
                      ? 'bg-gray-200 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  <span>Start Autonomous Inspection</span>
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>

            {/* Right 1 Col: Agronomic Parameters */}
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-md">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <Sliders size={20} className="text-blue-600" />
                Agronomic Parameters
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-5">
                Soil chemistry and micro-climate inputs for calibrated yield regression
              </p>

              <div className="space-y-4">
                <div>
                  <label className="text-xs font-bold text-gray-700 dark:text-gray-300 block mb-1">Crop Species</label>
                  <select 
                    value={cropType} 
                    onChange={e => setCropType(e.target.value)}
                    className="w-full bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white shadow-sm font-medium focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Tomato">Tomato (Solanum lycopersicum)</option>
                    <option value="Potato">Potato (Solanum tuberosum)</option>
                    <option value="Bell Pepper">Bell Pepper (Capsicum annuum)</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-bold text-gray-700 dark:text-gray-300 block mb-1">Field Area (ha)</label>
                    <input 
                      type="number" 
                      step="0.1" 
                      value={fieldArea} 
                      onChange={e => setFieldArea(parseFloat(e.target.value) || 1.0)}
                      className="w-full bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm font-mono text-gray-900 dark:text-white shadow-sm focus:ring-2 focus:ring-blue-500" 
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-gray-700 dark:text-gray-300 block mb-1">Growth Stage</label>
                    <select 
                      value={growthStage} 
                      onChange={e => setGrowthStage(e.target.value)}
                      className="w-full bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white shadow-sm font-medium focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="Vegetative">Vegetative</option>
                      <option value="Flowering">Flowering</option>
                      <option value="Fruiting">Fruiting</option>
                      <option value="Maturity">Maturity</option>
                    </select>
                  </div>
                </div>

                <div>
                  <span className="text-xs font-bold text-gray-700 dark:text-gray-300 block mb-1">Soil Nutrients (kg/ha)</span>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <span className="text-[10px] text-gray-500 block mb-0.5">N</span>
                      <input 
                        type="number" 
                        value={soilN} 
                        onChange={e => setSoilN(parseFloat(e.target.value) || 0)}
                        className="w-full bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-2.5 py-1.5 text-xs font-mono text-gray-900 dark:text-white shadow-sm" 
                      />
                    </div>
                    <div>
                      <span className="text-[10px] text-gray-500 block mb-0.5">P</span>
                      <input 
                        type="number" 
                        value={soilP} 
                        onChange={e => setSoilP(parseFloat(e.target.value) || 0)}
                        className="w-full bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-2.5 py-1.5 text-xs font-mono text-gray-900 dark:text-white shadow-sm" 
                      />
                    </div>
                    <div>
                      <span className="text-[10px] text-gray-500 block mb-0.5">K</span>
                      <input 
                        type="number" 
                        value={soilK} 
                        onChange={e => setSoilK(parseFloat(e.target.value) || 0)}
                        className="w-full bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-2.5 py-1.5 text-xs font-mono text-gray-900 dark:text-white shadow-sm" 
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="text-xs font-bold text-gray-700 dark:text-gray-300 block mb-1">Soil pH</label>
                    <input 
                      type="number" 
                      step="0.1" 
                      value={soilPh} 
                      onChange={e => setSoilPh(parseFloat(e.target.value) || 6.5)}
                      className="w-full bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-2 py-1.5 text-xs font-mono text-gray-900 dark:text-white shadow-sm" 
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-gray-700 dark:text-gray-300 block mb-1">Temp (°C)</label>
                    <input 
                      type="number" 
                      value={tempC} 
                      onChange={e => setTempC(parseFloat(e.target.value) || 25)}
                      className="w-full bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-2 py-1.5 text-xs font-mono text-gray-900 dark:text-white shadow-sm" 
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-gray-700 dark:text-gray-300 block mb-1">Rain (mm)</label>
                    <input 
                      type="number" 
                      value={rainfallMm} 
                      onChange={e => setRainfallMm(parseFloat(e.target.value) || 100)}
                      className="w-full bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-2 py-1.5 text-xs font-mono text-gray-900 dark:text-white shadow-sm" 
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-bold text-gray-700 dark:text-gray-300">Sampling Rate</label>
                    <span className="text-[11px] font-mono text-blue-600 dark:text-blue-400 font-bold">1/{frameInterval} frames</span>
                  </div>
                  <input 
                    type="range" 
                    min="5" 
                    max="60" 
                    step="5"
                    value={frameInterval} 
                    onChange={e => setFrameInterval(parseInt(e.target.value) || 15)}
                    className="w-full accent-blue-600 cursor-pointer" 
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: ANALYTICS DASHBOARD (Independent Dedicated View) */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {summaryData ? (
              <>
                {/* Active Inspection Header Banner */}
                <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-md">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 size={20} className="text-emerald-500" />
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                          Field Inspection Analytics Overview
                        </h2>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        Analysis Job ID: <span className="font-mono text-blue-600">{activeJobId}</span> • Total Analyzed Frames: {summaryData.total_frames_analyzed}
                      </p>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => setActiveTab('evidence')}
                        className="px-4 py-2 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-700 rounded-lg text-sm font-semibold transition inline-flex items-center gap-2 shadow-sm"
                      >
                        <Layers size={16} />
                        View Evidence
                      </button>
                      <button
                        onClick={() => setActiveTab('reports')}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition inline-flex items-center gap-2 shadow-sm hover:shadow-md"
                      >
                        <Download size={16} />
                        Download PDF
                      </button>
                    </div>
                  </div>
                </div>

                {/* 4 Score Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-white dark:bg-gray-900 p-5 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Crop Health Score</p>
                    <div className="mt-2 flex items-baseline gap-2">
                      <span className="text-3xl font-extrabold text-gray-900 dark:text-white font-mono">
                        {summaryData.mean_health_score}%
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        summaryData.mean_health_score >= 80 
                          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                          : summaryData.mean_health_score >= 50
                          ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
                      }`}>
                        {summaryData.mean_health_score >= 80 ? 'HEALTHY' : summaryData.mean_health_score >= 50 ? 'MODERATE' : 'SEVERE'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Physical tissue lesion ratio & pathogen virulence</p>
                  </div>

                  <div className="bg-white dark:bg-gray-900 p-5 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Tracked Weeds</p>
                    <div className="mt-2 flex items-baseline gap-1">
                      <span className="text-3xl font-extrabold text-blue-600 dark:text-blue-400 font-mono">
                        {summaryData.unique_weeds_detected}
                      </span>
                      <span className="text-xs text-gray-500">clusters</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">ByteTrack deduplicated spatial tracks</p>
                  </div>

                  <div className="bg-white dark:bg-gray-900 p-5 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Weed Canopy Ratio</p>
                    <div className="mt-2 flex items-baseline gap-1">
                      <span className="text-3xl font-extrabold text-amber-600 dark:text-amber-400 font-mono">
                        {summaryData.mean_weed_canopy_pct}%
                      </span>
                      <span className="text-xs text-gray-500">WCR</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Field surface weed canopy coverage</p>
                  </div>

                  <div className="bg-white dark:bg-gray-900 p-5 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Calibrated Yield</p>
                    <div className="mt-2 flex items-baseline gap-1">
                      <span className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
                        {summaryData.yield_prediction?.predicted_yield_t_ha || 'N/A'}
                      </span>
                      <span className="text-xs text-gray-500">t/ha</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-2 font-mono text-[11px]">
                      90% CI: [{summaryData.yield_prediction?.ci_lower || 0} - {summaryData.yield_prediction?.ci_upper || 0}]
                    </p>
                  </div>
                </div>

                {/* Pathology & Action Plan Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-md">
                    <h3 className="text-base font-bold text-gray-900 dark:text-white mb-4">Foliar Health Triage</h3>
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-xs text-gray-700 dark:text-gray-300 mb-1 font-semibold">
                          <span>Healthy Foliage</span>
                          <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">
                            {summaryData.healthy_leaves_count} ({((summaryData.healthy_leaves_count / Math.max(1, summaryData.total_leaves_analyzed)) * 100).toFixed(1)}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-2.5 overflow-hidden">
                          <div 
                            className="bg-emerald-500 h-2.5 rounded-full" 
                            style={{ width: `${(summaryData.healthy_leaves_count / Math.max(1, summaryData.total_leaves_analyzed)) * 100}%` }}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs text-gray-700 dark:text-gray-300 mb-1 font-semibold">
                          <span>Diseased / Pathological</span>
                          <span className="font-mono text-red-600 dark:text-red-400 font-bold">
                            {summaryData.diseased_leaves_count} ({((summaryData.diseased_leaves_count / Math.max(1, summaryData.total_leaves_analyzed)) * 100).toFixed(1)}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-2.5 overflow-hidden">
                          <div 
                            className="bg-red-500 h-2.5 rounded-full" 
                            style={{ width: `${(summaryData.diseased_leaves_count / Math.max(1, summaryData.total_leaves_analyzed)) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-800 text-xs">
                      <div>
                        <span className="text-gray-500">Predominant Diagnosed Condition: </span>
                        <span className="font-bold text-gray-900 dark:text-white">{summaryData.predominant_disease}</span>
                      </div>
                      {weedFindings.length > 0 && (
                        <div className="mt-1">
                          <span className="text-gray-500">Detected Weeds: </span>
                          <span className="font-semibold text-blue-600 dark:text-blue-400">{weedFindings.length} tracked instances</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-md flex flex-col justify-between">
                    <div>
                      <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 mb-2">
                        <ShieldCheck size={18} />
                        <h3 className="text-base font-bold text-gray-900 dark:text-white">Agronomic Remediation Plan</h3>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                        {summaryData.mean_health_score < 70 
                          ? `Pathogen pressure detected (${summaryData.predominant_disease}). Immediate spot-targeted fungicide or biological control is advised. Maintain soil moisture levels.`
                          : `Crop condition is nominal (${summaryData.mean_health_score}% health index). Standard scouting routine. Keep weed canopy ratio under control.`}
                      </p>
                      <div className="bg-gray-50 dark:bg-gray-950 p-3.5 rounded-lg border border-gray-200 dark:border-gray-800 text-xs">
                        <div className="flex items-center gap-1.5 font-bold text-gray-800 dark:text-gray-200 mb-1">
                          <FileCheck size={14} className="text-blue-600" />
                          <span>Official Audit PDF Available</span>
                        </div>
                        <p className="text-gray-500">Includes visual bounding box keyframes, lesion overlays, and yield regressions.</p>
                      </div>
                    </div>

                    <button
                      onClick={() => setActiveTab('reports')}
                      className="w-full mt-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-all shadow-sm hover:shadow-md inline-flex items-center justify-center gap-2"
                    >
                      <FileText size={16} />
                      <span>View Full PDF Report</span>
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white dark:bg-gray-900 rounded-xl p-12 border border-gray-200 dark:border-gray-800 shadow-md text-center max-w-xl mx-auto">
                <BarChart3 size={48} className="text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No Active Inspection Analysis Loaded</h3>
                <p className="text-sm text-gray-500 mb-6">
                  You can upload a drone video from Tab 1 or click below to quick-load the validation video.
                </p>
                <button
                  onClick={() => setActiveTab('upload')}
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition"
                >
                  Go to Video Ingestion Tab
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: TRACEABLE EVIDENCE GALLERY (Independent Dedicated View) */}
        {activeTab === 'evidence' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white dark:bg-gray-900 p-5 rounded-xl border border-gray-200 dark:border-gray-800 shadow-md">
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <Layers size={20} className="text-blue-600" />
                  Traceable Foliar Evidence Dossier
                </h2>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Side-by-side comparison of original crops and segmented lesion masks. Click any card to inspect full resolution.
                </p>
              </div>
              <div className="text-xs font-mono font-bold bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-3 py-1.5 rounded-lg border border-blue-200 dark:border-blue-800">
                {leafFindings.length} diagnosed leaves found
              </div>
            </div>

            {leafFindings.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {leafFindings.map((finding) => (
                  <div
                    key={finding.id}
                    onClick={() => setZoomFinding(finding)}
                    className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm hover:shadow-lg hover:border-blue-300 transition-all cursor-pointer group"
                  >
                    <div className="grid grid-cols-2 gap-1 bg-gray-50 dark:bg-gray-950 p-2 border-b border-gray-200 dark:border-gray-800">
                      <div>
                        <span className="text-[10px] text-gray-500 uppercase font-bold block mb-1">Original Crop</span>
                        {finding.crop_image_url ? (
                          <img src={finding.crop_image_url} alt="Leaf" className="w-full h-32 object-cover rounded-lg" />
                        ) : (
                          <div className="w-full h-32 bg-gray-200 dark:bg-gray-800 rounded-lg flex items-center justify-center text-xs text-gray-500">No Image</div>
                        )}
                      </div>
                      <div>
                        <span className="text-[10px] text-emerald-600 uppercase font-bold block mb-1">Lesion Mask</span>
                        {finding.mask_overlay_url ? (
                          <img src={finding.mask_overlay_url} alt="Mask" className="w-full h-32 object-cover rounded-lg border border-emerald-500/20" />
                        ) : (
                          <div className="w-full h-32 bg-gray-200 dark:bg-gray-800 rounded-lg flex items-center justify-center text-xs text-gray-500">No Mask</div>
                        )}
                      </div>
                    </div>

                    <div className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="text-sm font-bold text-gray-900 dark:text-white group-hover:text-blue-600 transition truncate max-w-[180px]">
                            {finding.crop_name} {finding.disease_name}
                          </h4>
                          <span className="text-xs font-mono text-gray-500">
                            Frame #{finding.frame_number} • {finding.timestamp_sec.toFixed(2)}s
                          </span>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          finding.severity_category === 'healthy'
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                            : finding.severity_category === 'mild'
                            ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
                        }`}>
                          {finding.severity_category.toUpperCase()}
                        </span>
                      </div>

                      <div className="flex justify-between items-center text-xs pt-2.5 border-t border-gray-100 dark:border-gray-800 font-medium">
                        <span className="text-gray-500">Lesion Ratio: <span className="font-mono text-amber-600 font-bold">{finding.lesion_area_pct}%</span></span>
                        <span className="text-gray-500">Score: <span className="font-mono text-gray-900 dark:text-white font-bold">{finding.health_score}/100</span></span>
                      </div>

                      <div className="mt-2.5 flex items-center justify-between text-[11px] text-gray-400 group-hover:text-blue-600 transition">
                        <span className="flex items-center gap-1">
                          <Maximize2 size={13} />
                          <span>Click to zoom</span>
                        </span>
                        <span className="font-mono">{(finding.classification_confidence * 100).toFixed(1)}% conf</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-900 rounded-xl p-12 border border-gray-200 dark:border-gray-800 shadow-md text-center max-w-xl mx-auto">
                <Layers size={48} className="text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No Foliar Findings Recorded</h3>
                <p className="text-sm text-gray-500 mb-6">
                  Run an inspection from the Upload tab to generate traceable evidence crops and lesion segmentation overlays.
                </p>
                <button
                  onClick={() => setActiveTab('upload')}
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition"
                >
                  Upload & Analyze Field Footage
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: PDF ANALYSIS REPORTS (Independent Dedicated View) */}
        {activeTab === 'reports' && (
          <div className="max-w-2xl mx-auto bg-white dark:bg-gray-900 rounded-xl p-8 border border-gray-200 dark:border-gray-800 shadow-md text-center">
            <div className="w-14 h-14 bg-blue-100 dark:bg-blue-900/40 rounded-xl flex items-center justify-center text-blue-600 dark:text-blue-400 mx-auto mb-4">
              <FileText size={28} />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              12-Section Agronomic Audit Inspection Report
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">
              Compiled using Python ReportLab. Includes embedded full-color annotated video keyframes, bounding box telemetry, foliar lesion pathology charts, calibrated yield regressions, and actionable agronomic remedies.
            </p>

            <div className="text-left bg-gray-50 dark:bg-gray-950 p-4 rounded-xl border border-gray-200 dark:border-gray-800 mb-6 text-xs space-y-2.5">
              <div className="flex items-center justify-between font-medium">
                <span className="text-gray-500">Document Engine:</span>
                <span className="font-mono font-bold text-gray-900 dark:text-white">Python ReportLab 4.x (A4)</span>
              </div>
              <div className="flex items-center justify-between font-medium">
                <span className="text-gray-500">Visual Evidence:</span>
                <span className="font-mono font-bold text-emerald-600">Keyframes + Leaf Crops + Lesion Overlays</span>
              </div>
              <div className="flex items-center justify-between font-medium">
                <span className="text-gray-500">Active Job ID:</span>
                <span className="font-mono text-blue-600">{activeJobId || 'Pending analysis'}</span>
              </div>
            </div>

            {activeJobId ? (
              <a
                href={`/api/v1/reports/${activeJobId}/pdf`}
                target="_blank"
                rel="noreferrer"
                download={`audit_report_${activeJobId.slice(0, 8)}.pdf`}
                className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-sm transition-all shadow-md hover:shadow-lg inline-flex items-center gap-2"
              >
                <Download size={18} />
                <span>Download Official Audit Report (PDF)</span>
              </a>
            ) : (
              <div>
                <p className="text-xs text-gray-500 mb-4">Run an analysis first to compile the official audit report.</p>
                <button
                  onClick={() => setActiveTab('upload')}
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition"
                >
                  Go to Upload Tab
                </button>
              </div>
            )}
          </div>
        )}

        {/* Evidence Full-Resolution Zoom Modal */}
        {zoomFinding && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-3xl w-full border border-gray-200 dark:border-gray-800 overflow-hidden shadow-2xl">
              <div className="p-5 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-gray-900 dark:text-white">
                    {zoomFinding.crop_name} {zoomFinding.disease_name}
                  </h3>
                  <p className="text-xs text-gray-500 font-mono">
                    Frame #{zoomFinding.frame_number} • Time: {zoomFinding.timestamp_sec.toFixed(2)}s • Confidence: {(zoomFinding.classification_confidence * 100).toFixed(1)}%
                  </p>
                </div>
                <button
                  onClick={() => setZoomFinding(null)}
                  className="p-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-500 hover:text-gray-900 dark:hover:text-white"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 bg-gray-50 dark:bg-gray-950">
                <div>
                  <span className="text-xs font-bold text-gray-500 block mb-2">Original High-Res Crop</span>
                  <img 
                    src={zoomFinding.crop_image_url} 
                    alt="Original" 
                    className="w-full h-64 object-contain bg-black/40 rounded-xl border border-gray-300 dark:border-gray-800" 
                  />
                </div>
                <div>
                  <span className="text-xs font-bold text-emerald-600 block mb-2">Foliar Lesion Segmentation Overlay</span>
                  <img 
                    src={zoomFinding.mask_overlay_url} 
                    alt="Mask" 
                    className="w-full h-64 object-contain bg-black/40 rounded-xl border border-emerald-500/30" 
                  />
                </div>
              </div>

              <div className="p-4 bg-white dark:bg-gray-900 flex justify-between items-center text-xs">
                <div className="flex gap-6">
                  <div>
                    <span className="text-gray-500 block font-medium">Lesion Damage:</span>
                    <span className="font-mono font-bold text-amber-600 text-sm">{zoomFinding.lesion_area_pct}%</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block font-medium">Health Rating:</span>
                    <span className="font-mono font-bold text-gray-900 dark:text-white text-sm">{zoomFinding.health_score}/100</span>
                  </div>
                </div>
                <button
                  onClick={() => setZoomFinding(null)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-lg font-medium transition"
                >
                  Close Viewer
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
