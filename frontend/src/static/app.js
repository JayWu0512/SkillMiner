// SkillMiner Agent Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysisForm');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const resultsSection = document.querySelector('.results-section');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading state
        loadingSpinner.style.display = 'block';
        resultsSection.style.display = 'none';
        
        // Prepare form data
        const formData = new FormData(form);
        
        try {
            // Submit to API
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Analysis failed');
            }
            
            const result = await response.json();
            
            // Display results
            displayResults(result);
            
        } catch (error) {
            console.error('Error:', error);
            alert('Analysis failed: ' + error.message);
        } finally {
            // Hide loading state
            loadingSpinner.style.display = 'none';
        }
    });
});

function displayResults(result) {
    // Update match score
    const matchScore = document.getElementById('matchScore');
    matchScore.textContent = result.match_score.toFixed(1) + '%';
    
    // Color code the match score
    if (result.match_score >= 80) {
        matchScore.className = 'match-score text-success';
    } else if (result.match_score >= 60) {
        matchScore.className = 'match-score text-warning';
    } else {
        matchScore.className = 'match-score text-danger';
    }
    
    // Update summary
    document.getElementById('matchSummary').innerHTML = `<p class="text-muted">${result.summary}</p>`;
    
    // Update job title
    document.getElementById('jobTitle').textContent = result.job_title || 'Position';
    
    // Display required skills
    displayRequiredSkills(result.required_skills);
    
    // Display existing skills
    displayExistingSkills(result.existing_skills);
    
    // Display missing skills
    displayMissingSkills(result.missing_skills);
    
    // Display skill gaps
    displaySkillGaps(result.skill_gaps);
    
    // Display recommendations
    displayRecommendations(result.recommendations);
    
    // Show results section
    document.querySelector('.results-section').style.display = 'block';
    
    // Scroll to results
    document.querySelector('.results-section').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

function displayRequiredSkills(skills) {
    const container = document.getElementById('requiredSkills');
    
    if (!skills || skills.length === 0) {
        container.innerHTML = '<p class="text-muted">No specific skills identified</p>';
        return;
    }
    
    let html = '';
    skills.forEach(skill => {
        const badgeClass = getBadgeClass(skill.importance);
        html += `<span class="skill-badge ${badgeClass}" title="${skill.context}">${skill.skill}</span>`;
    });
    
    container.innerHTML = html;
}

function displayExistingSkills(skills) {
    const container = document.getElementById('existingSkills');
    
    if (!skills || skills.length === 0) {
        container.innerHTML = '<p class="text-muted">No resume provided or no skills detected</p>';
        return;
    }
    
    let html = '';
    skills.forEach(skill => {
        const levelText = skill.level ? ` (${skill.level})` : '';
        const yearsText = skill.years_experience ? ` - ${skill.years_experience} years` : '';
        html += `<span class="skill-badge skill-existing" title="${skill.context}">${skill.name}${levelText}${yearsText}</span>`;
    });
    
    container.innerHTML = html;
}

function displayMissingSkills(skills) {
    const container = document.getElementById('missingSkills');
    
    if (!skills || skills.length === 0) {
        container.innerHTML = '<p class="text-success"><i class="fas fa-check me-2"></i>Great! You have all the required skills.</p>';
        return;
    }
    
    let html = '';
    skills.forEach(skill => {
        html += `<span class="skill-badge skill-missing">${skill}</span>`;
    });
    
    container.innerHTML = html;
}

function displaySkillGaps(gaps) {
    const container = document.getElementById('skillGaps');
    
    if (!gaps || gaps.length === 0) {
        container.innerHTML = '<p class="text-success"><i class="fas fa-check me-2"></i>No significant skill gaps identified!</p>';
        return;
    }
    
    let html = '';
    gaps.forEach(gap => {
        const gapClass = `gap-${gap.gap_severity}`;
        const severityIcon = getSeverityIcon(gap.gap_severity);
        
        html += `
            <div class="card mb-3 ${gapClass}">
                <div class="card-body">
                    <h6 class="card-title">
                        ${severityIcon} ${gap.skill}
                        <span class="badge bg-${getSeverityColor(gap.gap_severity)} ms-2">${gap.gap_severity}</span>
                    </h6>
                    <p class="card-text">
                        <strong>Required:</strong> ${gap.required_level || 'Not specified'} | 
                        <strong>Current:</strong> ${gap.current_level || 'None'}
                    </p>
                    <div class="recommendations">
                        <strong>Recommendations:</strong>
                        <ul class="mt-2">
                            ${gap.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendations');
    
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p class="text-muted">No specific recommendations available.</p>';
        return;
    }
    
    let html = '<ol class="list-group list-group-numbered">';
    recommendations.forEach(rec => {
        html += `<li class="list-group-item">${rec}</li>`;
    });
    html += '</ol>';
    
    container.innerHTML = html;
}

function getBadgeClass(importance) {
    switch (importance) {
        case 'required': return 'skill-required';
        case 'preferred': return 'skill-preferred';
        default: return 'skill-nice';
    }
}

function getSeverityIcon(severity) {
    switch (severity) {
        case 'critical': return '<i class="fas fa-exclamation-triangle text-danger"></i>';
        case 'moderate': return '<i class="fas fa-exclamation-circle text-warning"></i>';
        default: return '<i class="fas fa-info-circle text-info"></i>';
    }
}

function getSeverityColor(severity) {
    switch (severity) {
        case 'critical': return 'danger';
        case 'moderate': return 'warning';
        default: return 'info';
    }
}

// Add some interactive features
document.addEventListener('DOMContentLoaded', function() {
    // File upload feedback
    const fileInput = document.getElementById('resumeFile');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB
                console.log(`Selected file: ${file.name} (${fileSize} MB)`);
            }
        });
    }
    
    // Add tooltips to skill badges (if using Bootstrap tooltips)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (window.bootstrap) {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});