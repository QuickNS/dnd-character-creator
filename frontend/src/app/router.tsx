import { createBrowserRouter, Navigate } from "react-router-dom";
import { Home } from "@/pages/Home";
import { WizardIndex } from "@/pages/WizardIndex";
import { WizardStep } from "@/pages/WizardStep";
import { Sheet } from "@/pages/Sheet";
import { WizardLayout } from "@/components/layout/WizardLayout";

export const router = createBrowserRouter([
  { path: "/", element: <Home /> },
  {
    path: "/wizard",
    element: <WizardLayout />,
    children: [
      { index: true, element: <WizardIndex /> },
      { path: ":stepId", element: <WizardStep /> },
    ],
  },
  { path: "/sheet", element: <Sheet /> },
  { path: "*", element: <Navigate to="/" replace /> },
]);
