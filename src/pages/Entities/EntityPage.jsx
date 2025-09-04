import React from "react";
import EntitySection from "../../components/entity/EntitySection";

function EntityPage() {
  console.log("Rendering Entities Page");
  return (
    <div className="container-fluid p-4">
      {/* Bootstrap grid system for responsiveness */}
      <div className="row justify-content-center">
        <div className="col-lg-8 col-md-10 col-sm-12">
          <EntitySection />
        </div>
      </div>
    </div>
  );
}
export default EntityPage;
