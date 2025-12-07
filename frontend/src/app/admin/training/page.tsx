"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Database, Download, RefreshCw } from "lucide-react";
import { AdminSidebar } from "@/components/admin-sidebar";

interface FeedbackAnalytics {
  feedback_distribution: {
    total: number;
    positive: number;
    negative: number;
    positive_rate: number;
  };
  training_impact: {
    total_scored: number;
    training_candidates: number;
    awaiting_export: number;
    conversion_rate: string;
    average_quality_score: number;
  };
  score_distribution: {
    [key: string]: number;
  };
}

interface TrainingStats {
  total_scored: number;
  kept_for_training: number;
  exported: number;
  awaiting_export: number;
  average_score: number;
  score_distribution: {
    [key: string]: number;
  };
}

interface ClusterStats {
  total_clusters: number;
  active_clusters: number;
  pending_suggestions: number;
  total_queries_classified: number;
}

export default function TrainingMonitorPage() {
  const [feedbackData, setFeedbackData] = useState<FeedbackAnalytics | null>(null);
  const [trainingData, setTrainingData] = useState<TrainingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAnalytics = async () => {
    try {
      setRefreshing(true);

      const feedbackRes = await fetch("/api/v1/feedback/analytics");
      if (feedbackRes.ok) {
        setFeedbackData(await feedbackRes.json());
      }

      const trainingRes = await fetch("/api/v1/finetuning/stats");
      if (trainingRes.ok) {
        setTrainingData(await trainingRes.json());
      }
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    
    // Auto-refresh every 30 seconds for real-time monitoring
    const interval = setInterval(() => {
      fetchAnalytics();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const handleExport = async (format: string) => {
    try {
      const res = await fetch(`/api/v1/finetuning/export?format=${format}&min_score=4.0`, {
        method: "POST",
      });
      const data = await res.json();
      alert(`Exported ${data.exported_count} interactions!`);
      fetchAnalytics(); // Refresh stats
    } catch (error) {
      console.error("Export failed:", error);
      alert("Export failed. Check console.");
    }
  };

  const scoreLast7Days = async () => {
    try {
      const res = await fetch("/api/v1/finetuning/auto-score-all?days=7", { method: "POST" });
      const data = await res.json();
      alert(`Scored ${data.scored} interactions, ${data.saved_for_training} added to training dataset!`);
      fetchAnalytics();
    } catch (error) {
      console.error("Scoring failed:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500" />
          <p className="text-gray-600">Loading training metrics...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <AdminSidebar />
      <div className="ml-0 md:ml-5 transition-all duration-300">
        <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Training & Feedback Monitor</h1>
          <p className="text-gray-500 mt-1">Track model improvement and data quality</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={scoreLast7Days} variant="outline">
            Score Last 7 Days
          </Button>
          <Button onClick={fetchAnalytics} disabled={refreshing} variant="outline">
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Feedback</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{feedbackData?.feedback_distribution.total || 0}</div>
            <p className="text-xs text-green-600 mt-1">
              ↑ {feedbackData?.feedback_distribution.positive_rate.toFixed(1)}% positive
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Training Ready</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{feedbackData?.training_impact.training_candidates || 0}</div>
            <p className="text-xs text-gray-500 mt-1">
              Score: {feedbackData?.training_impact.average_quality_score.toFixed(2) || "N/A"}
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Awaiting Export</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{feedbackData?.training_impact.awaiting_export || 0}</div>
            <p className="text-xs text-gray-500 mt-1">Ready to fine-tune</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{feedbackData?.training_impact.conversion_rate || "0%"}</div>
            <p className="text-xs text-gray-500 mt-1">Feedback → Training</p>
          </CardContent>
        </Card>
      </div>

      {/* Export Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="w-5 h-5" />
            Export Training Dataset
          </CardTitle>
          <CardDescription>
            Export {feedbackData?.training_impact.awaiting_export || 0} high-quality interactions for fine-tuning
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Button onClick={() => handleExport("alpaca")} className="flex-1" size="lg">
              <Database className="w-4 h-4 mr-2" />
              Export Alpaca Format
            </Button>
            <Button onClick={() => handleExport("sharegpt")} variant="secondary" className="flex-1" size="lg">
              <Database className="w-4 h-4 mr-2" />
              Export ShareGPT Format
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Quality Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Quality Score Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {feedbackData?.score_distribution && Object.entries(feedbackData.score_distribution).map(([tier, count]) => {
                const percentage = (count / (feedbackData.training_impact.total_scored || 1)) * 100;
                return (
                  <div key={tier}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm capitalize">{tier.replace(/_/g, " ")}</span>
                      <span className="text-sm font-medium">{count}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Training Pipeline Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                <span className="text-sm">Total Interactions Scored</span>
                <Badge variant="outline">{trainingData?.total_scored || 0}</Badge>
              </div>
              <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                <span className="text-sm">Approved for Training</span>
                <Badge className="bg-green-600">{trainingData?.kept_for_training || 0}</Badge>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="text-sm">Already Exported</span>
                <Badge variant="secondary">{trainingData?.exported || 0}</Badge>
              </div>
              <div className="flex justify-between items-center p-3 bg-orange-50 rounded">
                <span className="text-sm">Pending Export</span>
                <Badge className="bg-orange-600">{trainingData?.awaiting_export || 0}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
        </div>
      </div>
    </>
  );
}
