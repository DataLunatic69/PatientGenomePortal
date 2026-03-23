import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/card';
import { Button } from '../ui/button';
import { UploadCloud, File, AlertCircle, Loader2, Sparkles, CheckCircle2 } from 'lucide-react';
import { Alert, AlertDescription } from '../ui/alert';
import { Progress } from '../ui/progress';

export default function UploadCard() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [simulateProgress, setSimulateProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Fake progress effect while uploading
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isUploading) {
      setSimulateProgress(0);
      interval = setInterval(() => {
        setSimulateProgress((prev) => {
          if (prev >= 90) return prev;
          const increment = Math.random() * 10;
          return Math.min(prev + increment, 90);
        });
      }, 500);
    } else {
      setSimulateProgress(0);
    }
    return () => clearInterval(interval);
  }, [isUploading]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      // Pass a default patient_id or allow it to be dynamic. 
      // Using the currently hardcoded from original implementation.
      const response = await api.uploadFile(file);
      setSimulateProgress(100);
      
      // Delay navigation slightly for 100% completion effect
      setTimeout(() => {
        navigate(`/progress/${response.job_id}`);
      }, 600);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload file. Please try again.');
      setIsUploading(false);
    }
  };

  const resetFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <Card className="w-full mx-auto shadow-2xl border-muted/60 bg-white/60 backdrop-blur-xl">
      <CardHeader className="pb-4">
        <CardTitle className="text-2xl text-center font-bold tracking-tight text-foreground">Upload Data</CardTitle>
        <CardDescription className="text-center text-base">
          Supported file types: VCF, CSV, or TXT
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        <div
          className={`relative overflow-hidden border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-300 ease-in-out ${
            dragActive 
              ? 'border-primary bg-primary/10 scale-[1.02] shadow-inner' 
              : file 
                ? 'border-primary/50 bg-primary/5' 
                : 'border-muted-foreground/30 hover:border-primary/60 hover:bg-muted/30'
          } ${isUploading ? 'pointer-events-none opacity-90' : ''}`}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".vcf,.vcf.gz,.csv,.txt"
            onChange={handleFileChange}
            disabled={isUploading}
          />
          
          {isUploading && (
            <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-10 flex flex-col items-center justify-center p-6 space-y-4 rounded-xl">
               <div className="relative">
                 <div className="absolute inset-0 border-4 border-primary/20 rounded-full animate-ping"></div>
                 <div className="relative bg-primary text-white p-4 rounded-full shadow-lg">
                   <Sparkles className="h-8 w-8 animate-pulse" />
                 </div>
               </div>
               <div className="space-y-2 w-full max-w-[80%]">
                 <p className="font-semibold text-primary animate-pulse text-lg">Parsing & Analyzing Sequence...</p>
                 <Progress value={simulateProgress} className="h-2 w-full bg-primary/20 backdrop-blur-sm" />
                 <p className="text-xs text-muted-foreground font-mono">{Math.round(simulateProgress)}% complete</p>
               </div>
            </div>
          )}

          {file && !isUploading ? (
            <div className="flex flex-col items-center space-y-4 animate-in fade-in zoom-in duration-300">
              <div className="relative">
                <div className="bg-green-100 p-4 rounded-full shadow-sm">
                  <File className="w-12 h-12 text-green-600" />
                </div>
                <div className="absolute -top-2 -right-2 bg-white rounded-full p-0.5 shadow-sm">
                  <CheckCircle2 className="w-6 h-6 text-green-500" />
                </div>
              </div>
              <div>
                <p className="font-semibold text-lg text-foreground truncate max-w-[250px]">{file.name}</p>
                <p className="text-sm font-medium text-muted-foreground mt-1">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-2 text-destructive border-destructive/20 hover:bg-destructive/10 hover:text-destructive z-20"
                onClick={resetFile}
              >
                Remove File
              </Button>
            </div>
          ) : !isUploading && (
            <div className="flex flex-col items-center space-y-4">
              <div className="p-4 bg-primary/5 rounded-full ring-8 ring-primary/5 transition-transform duration-500 ease-out group-hover:scale-110">
                <UploadCloud className={`w-12 h-12 transition-colors duration-300 ${dragActive ? 'text-primary' : 'text-primary/60'}`} />
              </div>
              <div>
                <p className="text-lg text-foreground font-medium mb-1">
                  <span className="text-primary hover:underline font-bold">Click to browse</span> or drag and drop
                </p>
                <p className="text-sm text-muted-foreground">
                  Up to 5GB maximum file size
                </p>
              </div>
            </div>
          )}
        </div>

        {error && (
          <Alert variant="destructive" className="mt-6 animate-in slide-in-from-top-2">
            <AlertCircle className="h-5 w-5" />
            <AlertDescription className="font-medium">{error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
      
      <CardFooter className="pt-2">
        <Button
          className={`w-full text-lg h-14 transition-all duration-300 shadow-md hover:shadow-lg ${isUploading ? 'bg-primary/90' : ''}`}
          size="lg"
          disabled={!file || isUploading}
          onClick={handleUpload}
        >
          {isUploading ? (
            <>
              <Loader2 className="mr-3 h-5 w-5 animate-spin" /> 
              Executing AI Pipeline...
            </>
          ) : (
            'Analyze Sequence Data'
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}
