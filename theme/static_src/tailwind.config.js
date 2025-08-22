module.exports = {
  content: [
    // Templates in the theme app
    '../templates/**/*.html',
    
    // Templates in other apps
    '../../JUDICO_HUB/templates/**/*.html',
    '../../admin_portal/templates/**/*.html',
    '../../lawyer_portal/templates/**/*.html',
    '../../client_management/templates/**/*.html',
    '../../client_portal/templates/**/*.html',
    '../../communication/templates/**/*.html',
    '../../compliance/templates/**/*.html',
    '../../document_repository/templates/**/*.html',
    '../../finance_management/templates/**/*.html',
    '../../governance/templates/**/*.html',
    '../../hr_management/templates/**/*.html',
    '../../task_management/templates/**/*.html',
    '../../transaction_support/templates/**/*.html',
    '../../aml_system/templates/**/*.html',
    
    // JavaScript files
    './src/**/*.js',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}