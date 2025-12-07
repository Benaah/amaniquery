"use client"

import { AgentMonitoring } from "@/components/AgentMonitoring"
import { AdminSidebar } from "@/components/admin-sidebar"

export default function AgentMonitoringPage() {
  return (
    <>
      <AdminSidebar />
      <div className="ml-0 md:ml-5 transition-all duration-300">
        <div className="container mx-auto py-6 px-4">
          <AgentMonitoring />
        </div>
      </div>
    </>
  )
}
